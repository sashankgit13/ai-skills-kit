#!/usr/bin/env python3
"""Guided setup for staff: installs the AI skills (guidelines) and offers optional safety settings.

Everything is opt-in. The skills are the main point; the safety settings are optional extras
each person can accept, skip, change or undo at any time.

Most people start it by double-clicking "Start AI Setup" in the kit folder.
It can also be run from a terminal:

    python3 tools/setup.py                 # interactive, asks before every change
    python3 tools/setup.py --dry-run       # show what would change, change nothing
    python3 tools/setup.py --yes --tools claude-code,cursor   # accept recommended choices
    python3 tools/setup.py --skills-only                      # guidelines only, no settings step

What it changes (only for the person running it):
    ~/.claude/settings.json      Claude Code safety settings (merged, never overwritten)
    ~/.codex/config.toml         Codex safety defaults (merged, never overwritten)
    ~/.agents/skills, ~/.claude/skills   the skills themselves
    ~/ai-safety-setup/           summary, Cursor checklist, files to upload to the Claude app
Every file it edits is backed up first. Settings someone already chose are left alone.
Standard library only (Python 3.9+; Codex step needs 3.11+).
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import platform
import re
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import install  # noqa: E402
from validate_skill import find_skills, parse_frontmatter  # noqa: E402

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

KIT = HERE.parent
SKILLS_DIR = KIT / "skills"
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
LINE = "-" * 64

TOOLS = [
    ("claude-app", "Claude app (chat on web, desktop or phone)"),
    ("claude-code", "Claude Code (AI that works in a terminal or code editor)"),
    ("codex", "Codex (OpenAI's coding agent)"),
    ("cursor", "Cursor (AI code editor)"),
]
CODING_TOOLS = {"claude-code", "codex", "cursor"}

SKILL_INFO = {
    "guided-ai-use": (
        "Plain-language guidance: the AI explains its plan, asks before changing or sending "
        "anything, protects personal data, and tells you what to check afterwards.",
        "everyone",
    ),
    "secure-coding-baseline": (
        "Security rules: keep passwords and keys private, ignore instructions hidden in "
        "files or web pages, ask before deleting, deploying or installing.",
        "anyone who lets AI work on code or files",
    ),
    "disciplined-coding": (
        "Quality rules for code: small focused changes, no over-building, and proof "
        "(tests) before saying the work is done.",
        "people who write or review code",
    ),
}


# ---------------------------------------------------------------- talking to the user

class UI:
    def __init__(self, assume_yes: bool):
        self.assume_yes = assume_yes

    @staticmethod
    def say(text: str = "") -> None:
        print(text)

    def heading(self, text: str) -> None:
        print(f"\n{LINE}\n{text}\n{LINE}")

    def _input(self, prompt: str) -> str | None:
        if self.assume_yes:
            print(prompt + "(using recommended answer)")
            return None
        try:
            return input(prompt).strip()
        except EOFError:
            print("(no answer, using recommended)")
            return None

    def yes_no(self, question: str, default: bool = True) -> bool:
        hint = "[Y/n]" if default else "[y/N]"
        while True:
            ans = self._input(f"{question} {hint} ")
            if ans is None or ans == "":
                return default
            if ans.lower() in ("y", "yes"):
                return True
            if ans.lower() in ("n", "no"):
                return False
            print("  Please type y (yes) or n (no), or press Enter for the recommended answer.")

    def pick(self, question: str, options: list[tuple[str, str]], default: list[str]) -> list[str]:
        for i, (_, label) in enumerate(options, 1):
            mark = "*" if options[i - 1][0] in default else " "
            print(f"  {i}. [{mark}] {label}")
        print("  (* = recommended)")
        while True:
            ans = self._input(f"{question} Type numbers separated by commas, or press Enter for *: ")
            if ans is None or ans == "":
                return list(default)
            try:
                nums = sorted({int(x) for x in re.split(r"[,\s]+", ans) if x})
                if nums and all(1 <= n <= len(options) for n in nums):
                    return [options[n - 1][0] for n in nums]
            except ValueError:
                pass
            print(f"  Please type numbers between 1 and {len(options)}, for example: 1,3")


# ---------------------------------------------------------------- safety settings

class Setting:
    """One safety setting: a plain explanation plus the change it makes."""

    def __init__(self, key, tool, title, what, why, default=True, caution=None):
        self.key, self.tool, self.title = key, tool, title
        self.what, self.why, self.default, self.caution = what, why, default, caution


def claude_settings(system: str) -> list[Setting]:
    sandbox_caution = None
    if system == "Linux":
        sandbox_caution = "On Linux this needs two small programs (bubblewrap and socat). Ask IT if unsure."
    elif system == "Windows":
        sandbox_caution = "On Windows this only works inside WSL. Say no unless IT has set that up."
    return [
        Setting("claude.block_secrets", "claude-code",
                "Keep password and key files away from the AI",
                "Claude Code will not open or edit files that usually hold passwords, keys and "
                "access tokens (.env files, key files, your SSH and cloud login folders).",
                "These files can unlock company systems. If the AI reads them, their contents "
                "end up in the conversation."),
        Setting("claude.no_bypass", "claude-code",
                "Never allow 'skip all permission questions' mode",
                "Turns off the mode where Claude Code acts without asking you first.",
                "That mode removes your chance to stop a mistake or a trick hidden in a file."),
        Setting("claude.ask_risky", "claude-code",
                "Always ask before deleting files or publishing code",
                "Claude Code will ask you every time before deleting files, pushing code to a "
                "shared repository, or throwing away changes.",
                "These actions are hard or impossible to undo."),
        Setting("claude.sandbox", "claude-code",
                "Run the AI's commands inside a safety box",
                "Commands the AI runs are limited to your project folder and to websites you "
                "approve.",
                "Even if the AI is tricked, the damage stays contained.",
                default=(system == "Darwin"), caution=sandbox_caution),
    ]


def codex_settings() -> list[Setting]:
    return [
        Setting("codex.workspace_ask", "codex",
                "Only work in the opened project, and ask before anything else",
                "Codex may change files in the project you opened, and must ask before going "
                "outside it.",
                "Keeps the AI from touching other folders or settings on your computer."),
        Setting("codex.no_network", "codex",
                "Ask before the AI's commands use the internet",
                "Commands Codex runs cannot reach the internet unless you approve.",
                "Stops data from being sent out, or unknown software being downloaded, without "
                "you knowing."),
    ]


CLAUDE_DENY = [
    "Read(**/.env*)", "Edit(**/.env*)",
    "Read(**/secrets/**)", "Edit(**/secrets/**)",
    "Read(**/*.pem)", "Read(**/*.key)",
    "Read(~/.ssh/**)", "Read(~/.aws/**)",
]
CLAUDE_ASK = ["Bash(rm *)", "Bash(git push *)", "Bash(git reset --hard *)"]

CURSOR_CHECKLIST = [
    ("Privacy Mode is ON",
     "Your code and chats are not stored or used for training by Cursor-routed models."),
    ("Run Mode is NOT 'Run Everything'",
     "Choose a mode where Cursor asks or reviews before running commands."),
    ("Only approved MCP tools are connected",
     "Connected tools (MCP) can read and change things in other apps. Remove any you don't recognise."),
    ("Projects with secrets have a .cursorignore",
     "List .env and key files there. Note: this does not stop terminal commands, so keep real secrets off your laptop where possible."),
]


# ---------------------------------------------------------------- applying changes

def backup(path: Path, dry: bool) -> Path | None:
    if not path.exists():
        return None
    dest = path.with_name(f"{path.name}.bak-{STAMP}")
    if not dry:
        shutil.copy2(path, dest)
    return dest


def apply_claude(chosen: set[str], home: Path, dry: bool) -> list[str]:
    path = home / ".claude" / "settings.json"
    notes: list[str] = []
    data: dict = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            return [f"Skipped: {path} is not valid JSON, so I left it alone. Ask IT to check it."]
        if not isinstance(data, dict):
            return [f"Skipped: {path} has an unexpected format, so I left it alone."]
    before = json.dumps(data, sort_keys=True)
    perms = data.setdefault("permissions", {})

    def add_list(key: str, items: list[str], label: str):
        current = perms.setdefault(key, [])
        added = [i for i in items if i not in current]
        current.extend(added)
        notes.append(f"{label}: {'added ' + str(len(added)) + ' rule(s)' if added else 'already set'}")

    def set_once(container: dict, key: str, value, label: str):
        if key not in container:
            container[key] = value
            notes.append(f"{label}: turned on")
        elif container[key] == value:
            notes.append(f"{label}: already on")
        else:
            notes.append(f"{label}: you already have a different choice ({container[key]!r}); left it as is")

    if "claude.block_secrets" in chosen:
        add_list("deny", CLAUDE_DENY, "Block password/key files")
    if "claude.ask_risky" in chosen:
        add_list("ask", CLAUDE_ASK, "Ask before delete/publish")
    if "claude.no_bypass" in chosen:
        set_once(perms, "disableBypassPermissionsMode", "disable", "No skip-permissions mode")
    if "claude.sandbox" in chosen:
        set_once(data.setdefault("sandbox", {}), "enabled", True, "Safety box (sandbox)")
    if not perms:
        data.pop("permissions")

    if json.dumps(data, sort_keys=True) == before:
        return notes + ["No changes needed in Claude Code settings."]
    bak = backup(path, dry)
    if not dry:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    notes.append(("Would update " if dry else "Updated ") + str(path))
    if bak:
        notes.append(("Would back up the old file to " if dry else "Backup of the old file: ") + str(bak))
    return notes


def apply_codex(chosen: set[str], home: Path, dry: bool) -> list[str]:
    if tomllib is None:
        return ["Skipped Codex settings: this needs Python 3.11 or newer. Ask IT to apply them."]
    path = home / ".codex" / "config.toml"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    try:
        current = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return [f"Skipped: {path} could not be read, so I left it alone. Ask IT to check it."]

    notes: list[str] = []
    top_lines: list[str] = []
    new_text = text

    if "codex.workspace_ask" in chosen:
        for key, value, label in (("sandbox_mode", "workspace-write", "Work only in the project"),
                                  ("approval_policy", "on-request", "Ask before going further")):
            if key not in current:
                top_lines.append(f'{key} = "{value}"')
                notes.append(f"{label}: turned on")
            elif current[key] == value:
                notes.append(f"{label}: already on")
            else:
                notes.append(f"{label}: you already have {key} = {current[key]!r}; left it as is")

    if "codex.no_network" in chosen:
        table = current.get("sandbox_workspace_write")
        label = "Ask before using the internet"
        if not isinstance(table, dict):
            new_text = new_text.rstrip("\n") + ("\n\n" if new_text.strip() else "") + \
                "# Added by AI skills kit setup\n[sandbox_workspace_write]\nnetwork_access = false\n"
            notes.append(f"{label}: turned on")
        elif "network_access" not in table:
            new_text, n = re.subn(r"(?m)^\[sandbox_workspace_write\][ \t]*$",
                                  "[sandbox_workspace_write]\nnetwork_access = false", new_text, count=1)
            notes.append(f"{label}: turned on" if n else
                         f"{label}: could not place it safely; please ask IT")
        elif table["network_access"] is False:
            notes.append(f"{label}: already on")
        else:
            notes.append(f"{label}: you already allow internet access; left it as is")

    if top_lines:
        # Top-level keys must come before any [table] in TOML, so they go at the start.
        new_text = "# Added by AI skills kit setup\n" + "\n".join(top_lines) + "\n\n" + new_text

    if new_text == text:
        return notes + ["No changes needed in Codex settings."]
    try:
        tomllib.loads(new_text)  # never write a file Codex cannot read
    except tomllib.TOMLDecodeError:
        return notes + ["Stopped: the change would have broken the Codex settings file. Nothing was written."]
    bak = backup(path, dry)
    if not dry:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_text, encoding="utf-8")
    notes.append(("Would update " if dry else "Updated ") + str(path))
    if bak:
        notes.append(("Would back up the old file to " if dry else "Backup of the old file: ") + str(bak))
    return notes


def install_skills(skills: list[str], tools: set[str], dry: bool) -> tuple[bool, list[str]]:
    targets = []
    if "claude-code" in tools:
        targets.append("claude")
    if tools & {"codex", "cursor"}:
        targets.append("agents")
    if not targets:
        return True, []
    # --update refreshes skills that changed in the kit; copies someone edited are still kept.
    argv = ["install", "--global", "--update", "--targets", ",".join(targets)]
    for s in skills:
        argv += ["--skill", s]
    if dry:
        argv.append("--dry-run")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = install.main(argv)
    out = buf.getvalue()
    notes = []
    for line in out.splitlines():
        m = re.match(r"^(\S+)\s+(\S+)\s+->\s+(.+?)\s+\[(.+)\]$", line)
        if m:
            notes.append(f"{m.group(1)} -> {m.group(3)} ({m.group(4)})")
    if code != 0:
        notes.append("Something went wrong. Technical details:\n" + out)
    return code == 0, notes


def build_app_zips(skills: list[str], out_dir: Path, dry: bool) -> list[str]:
    notes = []
    for name in skills:
        src = SKILLS_DIR / name
        dest = out_dir / f"{name}.zip"
        if not dry:
            out_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
                for p in sorted(src.rglob("*")):
                    if p.is_file() and "evals" not in p.relative_to(src).parts:
                        z.write(p, (Path(name) / p.relative_to(src)).as_posix())
        notes.append(("Would create " if dry else "Created ") + str(dest))
    return notes


# ---------------------------------------------------------------- main flow

def friendly_skills() -> list[tuple[str, str, str]]:
    rows = []
    for s in find_skills(SKILLS_DIR):
        what, who = SKILL_INFO.get(s.name, (None, "anyone"))
        if what is None:
            fm, _ = parse_frontmatter((s / "SKILL.md").read_text(encoding="utf-8"))
            what = fm.get("description", "")
        rows.append((s.name, what, who))
    order = list(SKILL_INFO)
    rows.sort(key=lambda r: order.index(r[0]) if r[0] in order else len(order))
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--yes", action="store_true", help="accept recommended answers without asking")
    ap.add_argument("--dry-run", action="store_true", help="show what would change; change nothing")
    ap.add_argument("--tools", help="comma-separated: " + ", ".join(t for t, _ in TOOLS))
    ap.add_argument("--skills-only", action="store_true",
                    help="add the skills (guidelines) only; skip the optional settings step")
    args = ap.parse_args(argv)

    ui = UI(args.yes)
    home = Path.home()
    system = platform.system()
    out_dir = home / "ai-safety-setup"
    summary: list[str] = [f"# AI setup summary ({datetime.now():%Y-%m-%d %H:%M})", ""]
    if args.dry_run:
        summary.append("_Preview only (dry run): nothing was changed._\n")

    ui.heading("AI skills and safety setup")
    ui.say("This helper shares our team's AI guidelines with your AI tools:")
    ui.say("  1. Adds 'skills' - short rule books that guide how your AI assistant behaves.")
    ui.say("  2. Optionally, offers a few safety settings. These are suggestions only;")
    ui.say("     you can skip them, and change or undo them any time.")
    ui.say("It asks before every change. Nothing is sent anywhere. Files it edits are backed up first.")
    if args.dry_run:
        ui.say("\nPREVIEW MODE: I will show what would change, but change nothing.")

    # Step 1: tools
    ui.heading("Step 1 of 4: Which AI tools do you use?")
    if args.tools:
        tools = {t.strip() for t in args.tools.split(",") if t.strip()}
        bad = tools - {t for t, _ in TOOLS}
        if bad:
            print(f"Unknown tool(s): {', '.join(sorted(bad))}")
            return 2
        ui.say("Using: " + ", ".join(sorted(tools)))
    else:
        detected = [t for t, d in (("claude-code", ".claude"), ("codex", ".codex"), ("cursor", ".cursor"))
                    if (home / d).exists()]
        default = detected or ["claude-app"]
        if detected:
            ui.say("I found signs of: " + ", ".join(detected) + " on this computer.")
        tools = set(ui.pick("Which do you use?", TOOLS, default))
    summary += ["## Tools", *[f"- {label}" for t, label in TOOLS if t in tools], ""]

    # Step 2: skills
    ui.heading("Step 2 of 4: Choose skills")
    rows = friendly_skills()
    for name, what, who in rows:
        ui.say(f"- {name}\n    {what}\n    Recommended for: {who}")
    recommended = ["guided-ai-use"] if "guided-ai-use" in {r[0] for r in rows} else []
    if tools & CODING_TOOLS:
        recommended += [r[0] for r in rows if r[0] != "guided-ai-use"]
    ui.say("")
    skills = ui.pick("Which skills do you want?", [(r[0], r[0]) for r in rows], recommended)

    # Step 3: safety settings
    ui.heading("Step 3 of 4: Optional safety settings")
    chosen: set[str] = set()
    settings: list[Setting] = []
    if "claude-code" in tools:
        settings += claude_settings(system)
    if "codex" in tools:
        settings += codex_settings()
    show_settings = has_suggestions = bool(settings) or "cursor" in tools
    if not has_suggestions:
        ui.say("No settings to suggest for the tools you picked.")
    elif args.skills_only:
        ui.say("Skipped (guidelines only).")
        settings, show_settings = [], False
    else:
        ui.say("These are optional. The skills work on their own; the settings add a")
        ui.say("technical safety net for your own tools. You stay in control and can")
        ui.say("change or undo them later.")
        if not ui.yes_no("Would you like to look at them?", True):
            ui.say("OK, skipping the settings. Only the skills will be added.")
            settings, show_settings = [], False
        else:
            ui.say("For each one I'll explain what it does and why. Recommended answers are in capitals.")
    for s in settings:
        tool_label = dict(TOOLS)[s.tool].split(" (")[0]
        ui.say(f"\n[{tool_label}] {s.title}")
        ui.say(f"  What it does: {s.what}")
        ui.say(f"  Why it matters: {s.why}")
        if s.caution:
            ui.say(f"  Note: {s.caution}")
        if ui.yes_no("  Turn this on?", s.default):
            chosen.add(s.key)
    cursor_done: list[tuple[str, bool]] = []
    if "cursor" in tools and show_settings:
        ui.say("\n[Cursor] Cursor keeps its safety options in its own Settings screen,")
        ui.say("so I can't change them for you. Here are our suggestions (I'll save this list too):")
        for title, why in CURSOR_CHECKLIST:
            ui.say(f"\n  - {title}\n    {why}")
            cursor_done.append((title, ui.yes_no("    Is this already done?", False)))

    # Step 4: confirm and apply
    ui.heading("Step 4 of 4: Review and apply")
    ui.say("I'm about to:")
    if skills and tools & CODING_TOOLS:
        ui.say(f"  - add {len(skills)} skill(s) for: " + ", ".join(sorted(tools & CODING_TOOLS)))
    if skills and "claude-app" in tools:
        ui.say(f"  - prepare {len(skills)} skill file(s) for you to upload to the Claude app")
    for s in settings:
        if s.key in chosen:
            ui.say(f"  - turn on (optional setting): {s.title}")
    ui.say(f"  - save a summary in {out_dir}")
    if not ui.yes_no("\nGo ahead?", True):
        ui.say("OK, nothing was changed. You can run this again any time.")
        return 0

    results: list[tuple[str, list[str]]] = []
    ok = True
    if skills:
        good, notes = install_skills(skills, tools, args.dry_run)
        ok &= good
        if notes:
            results.append(("Skills for coding tools", notes))
        if "claude-app" in tools:
            results.append(("Skills for the Claude app",
                            build_app_zips(skills, out_dir / "claude-app-skills", args.dry_run)))
    if chosen & {s.key for s in settings if s.tool == "claude-code"}:
        results.append(("Claude Code safety settings", apply_claude(chosen, home, args.dry_run)))
    if chosen & {s.key for s in settings if s.tool == "codex"}:
        results.append(("Codex safety settings", apply_codex(chosen, home, args.dry_run)))

    ui.heading("Done" if not args.dry_run else "Preview finished")
    for title, notes in results:
        ui.say(f"\n{title}:")
        for n in notes:
            ui.say(f"  - {n}")
        summary += [f"## {title}", *[f"- {n}" for n in notes], ""]

    declined = [s.title for s in settings if s.key not in chosen]
    if declined:
        summary += ["## Optional settings you chose not to turn on", *[f"- {t}" for t in declined], ""]
    if cursor_done:
        summary += ["## Cursor suggestions (optional, in Cursor > Settings)",
                    *[f"- [{'x' if done else ' '}] {t}: {w}"
                      for (t, done), (_, w) in zip(cursor_done, CURSOR_CHECKLIST)], ""]

    next_steps = ["## Next steps"]
    if "claude-app" in tools and skills:
        next_steps.append(f"- Upload the files in `{out_dir / 'claude-app-skills'}` to the Claude app's "
                          "skills settings, or ask your admin to add them for the whole team.")
    if tools & CODING_TOOLS:
        next_steps.append("- Restart your AI tools so they pick up the new skills and settings.")
    if cursor_done and not all(d for _, d in cursor_done):
        next_steps.append(f"- If you like, go through the Cursor suggestions (saved in {out_dir / 'setup-summary.md'}).")
    next_steps += [
        "- Read GUIDE.md in the kit folder: one page on using AI agents safely.",
        "- Everything here is optional guidance. You can change these settings, or run this "
        "helper again to add the ones you skipped, at any time.",
        "- To undo: restore the backup files listed above, and remove the skills with "
        "`python3 tools/install.py uninstall --global`.",
    ]
    summary += next_steps
    ui.say("\n" + "\n".join(next_steps))

    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "setup-summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
        ui.say(f"\nA copy of this summary is saved in {out_dir / 'setup-summary.md'}")
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nStopped. Nothing further was changed.")
        sys.exit(130)
