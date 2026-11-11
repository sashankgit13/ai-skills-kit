#!/usr/bin/env python3
"""Install, check and remove kit skills in the folders Claude Code, Codex and Cursor read.

Discovery folders (project level / user level):
    agents  .agents/skills   ~/.agents/skills   Codex, Cursor and other Agent Skills clients
    claude  .claude/skills   ~/.claude/skills   Claude Code (Cursor also reads this folder)
    cursor  .cursor/skills   ~/.cursor/skills   Cursor only

Commands:
    install    validate, then copy (default) or symlink skills into the chosen folders
    status     compare installed skills with the kit: up to date, outdated, modified, missing
    uninstall  remove skills this kit installed (never touches skills it did not install)

Examples:
    python3 tools/install.py install   --project ~/code/my-app
    python3 tools/install.py install   --project ~/code/my-app --targets agents --link
    python3 tools/install.py status    --project ~/code/my-app
    python3 tools/install.py install   --project ~/code/my-app --update      # refresh outdated copies
    python3 tools/install.py uninstall --project ~/code/my-app --skill secure-coding-baseline
    python3 tools/install.py install   --global --targets agents,claude --dry-run

Installs are recorded in a lock file so status and uninstall know what the kit owns:
    project: <project>/.ai-skills-kit.lock.json  (commit it; no timestamps, sorted keys)
    global:  ~/.agents/.ai-skills-kit.lock.json
Change detection uses a SHA-256 over each file's relative path and contents, the same
idea as the Vercel skills CLI's project lock file. Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from validate_skill import find_skills, parse_frontmatter, validate  # noqa: E402

TARGETS = {
    "agents": Path(".agents/skills"),
    "claude": Path(".claude/skills"),
    "cursor": Path(".cursor/skills"),
}
DEFAULT_TARGETS = ["agents", "claude"]
SKILLS_DIR = HERE.parent / "skills"
LOCK_NAME = ".ai-skills-kit.lock.json"
LOCK_VERSION = 1
IGNORED = {".git", "__pycache__", ".DS_Store"}


# ---------- helpers ----------

def folder_hash(folder: Path) -> str:
    """SHA-256 over sorted relative paths and file contents. Ignores caches and VCS dirs."""
    h = hashlib.sha256()
    for path in sorted(folder.rglob("*")):
        rel = path.relative_to(folder)
        if any(part in IGNORED for part in rel.parts) or not path.is_file():
            continue
        h.update(rel.as_posix().encode("utf-8") + b"\0")
        h.update(path.read_bytes() + b"\0")
    return "sha256:" + h.hexdigest()


def skill_version(folder: Path) -> str:
    try:
        fm, _ = parse_frontmatter((folder / "SKILL.md").read_text(encoding="utf-8"))
    except Exception:
        return "?"
    meta = fm.get("metadata")
    return meta.get("version", "-") if isinstance(meta, dict) else "-"


def lock_path(base: Path, is_global: bool) -> Path:
    return (base / ".agents" / LOCK_NAME) if is_global else (base / LOCK_NAME)


def load_lock(path: Path) -> dict:
    if not path.is_file():
        return {"version": LOCK_VERSION, "skills": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"error: {path} is not valid JSON; fix or delete it")
        sys.exit(2)
    if data.get("version") != LOCK_VERSION:
        print(f"error: {path} has lock version {data.get('version')}, expected {LOCK_VERSION}")
        sys.exit(2)
    data.setdefault("skills", {})
    return data


def save_lock(path: Path, data: dict, dry: bool) -> None:
    if dry:
        return
    if not data["skills"]:
        if path.exists():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def remove_path(p: Path) -> None:
    if p.is_symlink() or p.is_file():
        p.unlink()
    elif p.exists():
        shutil.rmtree(p)


def resolve_base(args) -> Path:
    base = Path.home() if args.global_ else Path(args.project).expanduser().resolve()
    if not base.is_dir():
        print(f"error: {base} is not a directory")
        sys.exit(2)
    return base


def parse_targets(raw: str) -> list[str]:
    targets = [t.strip() for t in raw.split(",") if t.strip()]
    bad = [t for t in targets if t not in TARGETS]
    if bad:
        print(f"error: unknown target(s): {', '.join(bad)} (choose from {', '.join(TARGETS)})")
        sys.exit(2)
    return targets


def installed_state(dest: Path, recorded_hash: str | None, source: Path | None) -> str:
    """One word describing an installed copy relative to its lock entry and the kit source."""
    if dest.is_symlink():
        if not dest.exists():
            return "broken-link"
        return "linked"
    if not dest.exists():
        return "missing"
    current = folder_hash(dest)
    if recorded_hash and current != recorded_hash:
        return "modified"          # someone edited the installed copy
    if source is None:
        return "orphaned"          # skill no longer exists in the kit
    if current != folder_hash(source):
        return "outdated"          # kit has a newer version
    return "up-to-date"


# ---------- commands ----------

def cmd_install(args) -> int:
    base = resolve_base(args)
    targets = parse_targets(args.targets)
    skills = find_skills(SKILLS_DIR)
    if args.skill:
        missing = set(args.skill) - {s.name for s in skills}
        if missing:
            print(f"error: unknown skill(s): {', '.join(sorted(missing))}")
            return 2
        skills = [s for s in skills if s.name in set(args.skill)]
    if not skills:
        print("error: no skills to install")
        return 2

    blocked = False
    for skill in skills:
        errors, _ = validate(skill)
        if errors:
            blocked = True
            print(f"[blocked] {skill.name}: validation failed")
            for e in errors:
                print(f"   {e}")
    if blocked:
        return 1

    lpath = lock_path(base, args.global_)
    lock = load_lock(lpath)
    for skill in skills:
        src = skill.resolve()
        src_hash = folder_hash(src)
        entry = lock["skills"].get(skill.name, {"targets": {}})
        for target in targets:
            rel = TARGETS[target] / skill.name
            dest = base / rel
            exists = dest.exists() or dest.is_symlink()
            owned = target in entry["targets"]
            state = installed_state(dest, entry["targets"].get(target, {}).get("hash"), src) if exists else "missing"

            if exists and not owned and not args.force:
                result = "skipped (not installed by this kit; use --force to take over)"
            elif exists and state == "modified" and not args.force:
                result = "skipped (installed copy was edited; review, then use --force)"
            elif exists and state in ("up-to-date", "linked") and not args.force:
                result = "already current"
            elif exists and state == "outdated" and not (args.update or args.force):
                result = "outdated (use --update to refresh)"
            else:
                if args.dry_run:
                    result = "would link" if args.link else ("would update" if exists else "would copy")
                else:
                    if exists:
                        remove_path(dest)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if args.link:
                        os.symlink(src, dest, target_is_directory=True)
                    else:
                        shutil.copytree(src, dest, symlinks=False,
                                        ignore=shutil.ignore_patterns(*IGNORED))
                    result = "linked" if args.link else ("updated" if exists else "copied")
                entry["targets"][target] = {
                    "path": rel.as_posix(),
                    "mode": "link" if args.link else "copy",
                    "hash": None if args.link else src_hash,
                    "version": skill_version(src),
                }
            print(f"{skill.name:<26} {target:<7} -> {dest}  [{result}]")
        entry.pop("version", None)  # versions are tracked per target
        if entry["targets"]:
            lock["skills"][skill.name] = entry

    save_lock(lpath, lock, args.dry_run)
    if not args.dry_run:
        print(f"\nlock file: {lpath}")
    if "claude" in targets and ("agents" in targets or "cursor" in targets):
        print("note: Cursor also reads .claude/skills, so it may list a skill twice. "
              "Check your Cursor version, or install per tool with --targets.")
    return 0


def cmd_status(args) -> int:
    base = resolve_base(args)
    lpath = lock_path(base, args.global_)
    lock = load_lock(lpath)
    kit = {s.name: s.resolve() for s in find_skills(SKILLS_DIR)} if SKILLS_DIR.exists() else {}

    rows = []
    for name in sorted(set(lock["skills"]) | set(kit)):
        entry = lock["skills"].get(name)
        src = kit.get(name)
        if entry is None:
            rows.append((name, "-", "-", "not installed", skill_version(src) if src else "-"))
            continue
        for target, info in sorted(entry["targets"].items()):
            dest = base / info["path"]
            state = installed_state(dest, info.get("hash"), src)
            inst = skill_version(src) if (info.get("mode") == "link" and src) else info.get("version", "-")
            rows.append((name, target, inst, state,
                         skill_version(src) if src else "(removed from kit)"))

    if not rows:
        print("no skills in the kit and nothing installed")
        return 0
    print(f"{'skill':<26} {'target':<7} {'installed':<10} {'state':<14} kit")
    for name, target, inst, state, kitv in rows:
        print(f"{name:<26} {target:<7} {inst:<10} {state:<14} {kitv}")
    print(f"\nlock file: {lpath if lpath.exists() else '(none yet)'}")

    attention = {"outdated", "modified", "missing", "broken-link", "orphaned"}
    needs = [r for r in rows if r[3] in attention]
    if needs:
        print("\nnext steps:")
        if any(r[3] == "outdated" for r in needs):
            print("  outdated     -> install --update")
        if any(r[3] == "modified" for r in needs):
            print("  modified     -> review local edits, move them into the kit, then install --force")
        if any(r[3] == "missing" for r in needs):
            print("  missing      -> install (restores it), or uninstall to drop the lock entry")
        if any(r[3] == "broken-link" for r in needs):
            print("  broken-link  -> install --force --link (re-point it), or uninstall")
        if any(r[3] == "orphaned" for r in needs):
            print("  orphaned     -> uninstall --skill <name>")
    return 1 if (args.check and needs) else 0


def cmd_uninstall(args) -> int:
    base = resolve_base(args)
    lpath = lock_path(base, args.global_)
    lock = load_lock(lpath)
    if not lock["skills"]:
        print(f"nothing to uninstall (no lock entries in {lpath})")
        return 0

    names = args.skill or sorted(lock["skills"])
    unknown = [n for n in names if n not in lock["skills"]]
    if unknown:
        print(f"error: not installed by this kit: {', '.join(unknown)}")
        return 2
    only = set(parse_targets(args.targets)) if args.targets else None
    kit = {s.name: s.resolve() for s in find_skills(SKILLS_DIR)} if SKILLS_DIR.exists() else {}

    status = 0
    for name in names:
        entry = lock["skills"][name]
        for target in sorted(list(entry["targets"])):
            if only and target not in only:
                continue
            info = entry["targets"][target]
            dest = base / info["path"]
            state = installed_state(dest, info.get("hash"), kit.get(name))
            if state == "modified" and not args.force:
                result = "kept (installed copy was edited; use --force to delete anyway)"
                status = 1
            elif args.dry_run:
                result = "would remove" if (dest.exists() or dest.is_symlink()) else "would drop lock entry"
            else:
                existed = dest.exists() or dest.is_symlink()
                remove_path(dest)
                del entry["targets"][target]
                result = "removed" if existed else "lock entry dropped (folder was already gone)"
            print(f"{name:<26} {target:<7} -> {dest}  [{result}]")
        if not entry["targets"] and not args.dry_run:
            del lock["skills"][name]

    save_lock(lpath, lock, args.dry_run)
    return status


# ---------- CLI ----------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    def scope(sp):
        g = sp.add_mutually_exclusive_group(required=True)
        g.add_argument("--project", metavar="DIR", help="work on this project directory")
        g.add_argument("--global", dest="global_", action="store_true", help="work on your home directory")
        sp.add_argument("--dry-run", action="store_true", help="show what would happen without changing anything")

    i = sub.add_parser("install", help="validate and install skills")
    scope(i)
    i.add_argument("--targets", default=",".join(DEFAULT_TARGETS),
                   help=f"comma-separated: {', '.join(TARGETS)} (default {','.join(DEFAULT_TARGETS)})")
    i.add_argument("--skill", action="append", help="only this skill (repeatable); default: all")
    i.add_argument("--link", action="store_true", help="symlink instead of copying")
    i.add_argument("--update", action="store_true", help="refresh copies that are outdated")
    i.add_argument("--force", action="store_true",
                   help="replace even edited copies or folders this kit did not install")
    i.set_defaults(func=cmd_install)

    s = sub.add_parser("status", help="compare installed skills with the kit")
    scope(s)
    s.add_argument("--check", action="store_true", help="exit 1 if anything needs attention (for CI)")
    s.set_defaults(func=cmd_status)

    u = sub.add_parser("uninstall", help="remove skills this kit installed")
    scope(u)
    u.add_argument("--skill", action="append", help="only this skill (repeatable); default: all kit skills")
    u.add_argument("--targets", help="only these folders, comma-separated; default: all recorded")
    u.add_argument("--force", action="store_true", help="also delete copies that were edited locally")
    u.set_defaults(func=cmd_uninstall)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
