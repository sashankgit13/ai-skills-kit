#!/usr/bin/env python3
"""Validate skill folders against the agentskills.io format plus org portability rules.

Usage:
    python3 tools/validate_skill.py skills/            # every skill under a directory
    python3 tools/validate_skill.py skills/my-skill    # one skill

Exit code 0 = no errors (warnings allowed), 1 = at least one error.
Standard library only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ALLOWED_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_BODY_LINES = 500

# Heuristics only: they catch careless mistakes, not a determined attacker.
INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous|prior|above) instructions",
    r"disregard (all |any )?(previous|prior|above)",
    r"do not (tell|mention|reveal)[^.\n]{0,40}\buser\b",
    r"you are now (in )?(developer|admin|dan)",
]
SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS access key id"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key block"),
    (r"\bgh[pousr]_[A-Za-z0-9]{30,}\b", "GitHub token"),
    (r"\bsk-[A-Za-z0-9]{20,}\b", "API key (sk-...)"),
    (r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b", "Slack token"),
]
RISKY_SCRIPT_PATTERNS = [
    (r"(curl|wget)[^\n|]*\|\s*(ba|z)?sh", "pipes a download into a shell"),
    (r"\beval\s*\(", "uses eval"),
    (r"base64\s+(-d|--decode)", "decodes base64 (possible obfuscation)"),
    (r"\brm\s+-rf\s+(/|~)", "recursive delete of / or ~"),
]


class FrontmatterError(Exception):
    pass


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Minimal parser: `key: value` lines and one level of `metadata:` mapping."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError("file must start with a '---' frontmatter line")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise FrontmatterError("frontmatter is not closed with '---'") from None

    data: dict = {}
    current_map: str | None = None
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indented = raw.startswith((" ", "\t"))
        if indented:
            if current_map is None:
                raise FrontmatterError(f"unexpected indented line: {raw!r}")
            key, sep, value = raw.strip().partition(":")
            if not sep:
                raise FrontmatterError(f"bad metadata line: {raw!r}")
            data[current_map][key.strip()] = _unquote(value)
            continue
        key, sep, value = raw.partition(":")
        if not sep:
            raise FrontmatterError(f"bad frontmatter line: {raw!r}")
        key, value = key.strip(), value.strip()
        if key in data:
            raise FrontmatterError(f"duplicate field: {key}")
        if value == "" and key == "metadata":
            data[key] = {}
            current_map = key
        else:
            if value in (">", "|", ">-", "|-") or value.startswith(("[", "{")):
                raise FrontmatterError(
                    f"'{key}' must be a plain single-line string (no block scalars or lists)"
                )
            data[key] = _unquote(value)
            current_map = None
    return data, "\n".join(lines[end + 1:])


def validate(skill_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"{skill_dir}: missing SKILL.md"], warnings

    try:
        fm, body = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    except FrontmatterError as exc:
        return [f"{skill_md}: {exc}"], warnings
    except UnicodeDecodeError:
        return [f"{skill_md}: not valid UTF-8"], warnings

    where = str(skill_md)

    unknown = set(fm) - ALLOWED_FIELDS
    if unknown:
        errors.append(
            f"{where}: non-portable frontmatter field(s): {', '.join(sorted(unknown))} "
            f"(allowed: {', '.join(sorted(ALLOWED_FIELDS))})"
        )

    name = fm.get("name", "")
    if not name:
        errors.append(f"{where}: 'name' is required")
    else:
        if len(name) > 64:
            errors.append(f"{where}: name longer than 64 characters")
        if not NAME_RE.match(name):
            errors.append(f"{where}: name must be lowercase letters, digits and single hyphens")
        if name != skill_dir.name:
            errors.append(f"{where}: name '{name}' must match folder '{skill_dir.name}'")

    desc = fm.get("description", "")
    if not desc:
        errors.append(f"{where}: 'description' is required")
    else:
        if len(desc) > 1024:
            errors.append(f"{where}: description is {len(desc)} chars (max 1024)")
        if len(desc) < 40:
            warnings.append(f"{where}: description is very short; say what it does and when to use it")
        if not re.search(r"\b(use|when|if)\b", desc, re.IGNORECASE):
            warnings.append(f"{where}: description should say when to use the skill")

    if len(fm.get("compatibility", "")) > 500:
        errors.append(f"{where}: compatibility longer than 500 characters")
    if "allowed-tools" in fm:
        warnings.append(f"{where}: 'allowed-tools' is experimental and not honored by every agent")

    body_lines = body.splitlines()
    if len(body_lines) > MAX_BODY_LINES:
        warnings.append(f"{where}: body has {len(body_lines)} lines (recommended max {MAX_BODY_LINES})")
    if not body.strip():
        errors.append(f"{where}: body is empty")

    for rel in sorted(set(re.findall(r"\b((?:references|scripts|assets)/[\w./-]+)", body))):
        target = skill_dir / rel.rstrip(".,)")
        if not target.exists():
            errors.append(f"{where}: references missing file '{rel}'")

    # Content scans over every text file in the skill.
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pat in INJECTION_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                errors.append(f"{path}: possible prompt-injection phrase (/{pat}/)")
        for pat, label in SECRET_PATTERNS:
            if re.search(pat, text):
                errors.append(f"{path}: looks like it contains a secret ({label})")
        if "scripts" in path.parts:
            for pat, label in RISKY_SCRIPT_PATTERNS:
                if re.search(pat, text):
                    warnings.append(f"{path}: script {label}; needs human review")
    return errors, warnings


def find_skills(target: Path) -> list[Path]:
    if (target / "SKILL.md").is_file():
        return [target]
    return sorted(p.parent for p in target.rglob("SKILL.md"))


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    skills: list[Path] = []
    for arg in argv[1:]:
        path = Path(arg)
        if not path.exists():
            print(f"error: {arg} does not exist")
            return 2
        skills.extend(find_skills(path))
    if not skills:
        print("error: no SKILL.md files found")
        return 2

    seen: dict[str, Path] = {}
    total_errors = 0
    for skill in skills:
        errs, warns = validate(skill)
        name = skill.name
        if name in seen:
            errs.append(f"{skill}: duplicate skill name (also at {seen[name]})")
        seen[name] = skill
        status = "FAIL" if errs else "ok"
        print(f"[{status}] {skill}")
        for w in warns:
            print(f"   warning: {w}")
        for e in errs:
            print(f"   error:   {e}")
        total_errors += len(errs)
    print(f"\n{len(skills)} skill(s) checked, {total_errors} error(s)")
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
