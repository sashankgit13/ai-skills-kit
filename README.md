# AI skills kit

One skill format that works in Claude Code, Codex and Cursor, with a validator and an
installer that can also check versions and uninstall.

Skills follow the open [Agent Skills](https://agentskills.io) format: a folder with a
`SKILL.md` (YAML frontmatter + instructions) and optional `scripts/`, `references/`,
`assets/`. All three tools read this format; they differ only in **where** they look.

## Quick start

This kit **shares guidelines; it does not enforce anything.** Nobody is required to use the
optional settings, and everything can be changed or undone by the person who set it up.

**Staff (no technical knowledge needed):** double-click **Start AI Setup (Mac)** or
**Start AI Setup (Windows)** in this folder. It asks which AI tools you use, explains each
skill in plain words, then offers a few *optional* safety settings you can skip. It asks
before every change, backs up anything it edits, and saves a summary in
`~/ai-safety-setup/`. Then read `GUIDE.md`.
Needs Python 3.9+ (3.11+ for the Codex settings step). On macOS, the first run may need
right-click > Open because the launcher is not signed.

**Helping someone set up:** `python3 tools/setup.py --skills-only` adds just the
guidelines; `--yes --tools claude-code,codex` accepts the recommended answers.

**Developers / skill authors:** see Commands and Authoring rules below.

## Layout

```
Start AI Setup (Mac).command    double-click launchers for staff
Start AI Setup (Windows).bat
start-ai-setup.sh               same, for Linux
GUIDE.md                        one-page "using AI agents safely" for staff
skills/
  guided-ai-use/                plain-language guidance for non-technical users
  secure-coding-baseline/       security rules for agents + pre-merge checklist
  disciplined-coding/           small, simple, verified changes (Karpathy-style rules)
    SKILL.md                    what the agent reads
    references/                 loaded by the agent only when needed
    evals/EVALS.md              test scenarios for humans; not referenced by SKILL.md
templates/SKILL.template.md     copy this to start a new skill
templates/AGENTS.md             10-line always-loaded guideline file that points at the skills
tools/validate_skill.py         org checks: portability, secrets, injection, risky scripts
tools/install.py                install / status / uninstall, with a lock file
tools/setup.py                  guided setup behind the launchers (skills + optional settings)
ai-skills-test/                 A/B test of the skills (fake fixture, harness, results)
.github/workflows/              CI: org checks + official agentskills.io validator
```

## Where each tool looks (per vendor docs, checked Nov 2026)

| Tool | Project folder | User folder |
|---|---|---|
| Codex | `.agents/skills/` | `~/.agents/skills/` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Cursor | `.agents/skills/`, `.cursor/skills/` (also reads `.claude/skills/`, `.codex/skills/`) | `~/.agents/skills/`, `~/.cursor/skills/` |

## Commands

```bash
# check skills
python3 tools/validate_skill.py skills/

# install (copies into .agents/skills and .claude/skills by default)
python3 tools/install.py install --project ~/code/my-app --dry-run
python3 tools/install.py install --project ~/code/my-app
python3 tools/install.py install --project ~/code/my-app --targets cursor --link
python3 tools/install.py install --global --targets agents,claude

# see what is installed and whether it is current
python3 tools/install.py status --project ~/code/my-app
python3 tools/install.py status --project ~/code/my-app --check   # exit 1 if action needed

# refresh outdated copies
python3 tools/install.py install --project ~/code/my-app --update

# remove what the kit installed
python3 tools/install.py uninstall --project ~/code/my-app --skill disciplined-coding
python3 tools/install.py uninstall --project ~/code/my-app --dry-run
```

### Status values

| State | Meaning | What to do |
|---|---|---|
| `up-to-date` | Installed copy matches the kit | Nothing |
| `outdated` | The kit has a newer version | `install --update` |
| `modified` | Someone edited the installed copy | Review the edit, move it into the kit, then `install --force` |
| `missing` | Lock file lists it but the folder is gone | `install` restores it, or `uninstall` drops the entry |
| `linked` | Symlink to the kit (always current) | Nothing |
| `broken-link` | Symlink target moved | `install --force --link`, or `uninstall` |
| `orphaned` | Installed, but the skill was removed from the kit | `uninstall --skill <name>` |

### Safety behaviour
- A skill that fails validation is never installed.
- `install` will not overwrite a folder the kit did not install, or an installed copy someone
  edited, unless you pass `--force`.
- `uninstall` only removes what the lock file says the kit installed, and keeps edited copies
  unless you pass `--force`. Other skills in the same folders are never touched.
- `--dry-run` works for `install` and `uninstall`.

### Lock file
Installs are recorded in `<project>/.ai-skills-kit.lock.json` (commit it) or
`~/.agents/.ai-skills-kit.lock.json` for `--global`. Each installed folder stores its path,
mode, version and a SHA-256 over every file's relative path and contents. Keys are sorted
and there are no timestamps, to keep merge conflicts rare. This mirrors the approach of the
Vercel skills CLI's project lock file; the name is different so the two can coexist.

## Optional settings the guided setup can apply

Only for the person running it, only if they choose to look at the settings, and only for
the ones they say yes to. People can skip this step entirely (or use `--skills-only`):

| Tool | Setting (as shown to staff) | Technical change |
|---|---|---|
| Claude Code | Keep password and key files away from the AI | `permissions.deny` rules for `.env*`, `secrets/`, `*.pem`, `*.key`, `~/.ssh`, `~/.aws` in `~/.claude/settings.json` |
| Claude Code | Never allow "skip all permission questions" mode | `permissions.disableBypassPermissionsMode: "disable"` |
| Claude Code | Always ask before deleting files or publishing code | `permissions.ask` for `rm`, `git push`, `git reset --hard` |
| Claude Code | Run the AI's commands inside a safety box | `sandbox.enabled: true` (recommended on macOS only; needs extra tools on Linux, WSL on Windows) |
| Codex | Only work in the opened project, and ask before anything else | `sandbox_mode = "workspace-write"`, `approval_policy = "on-request"` in `~/.codex/config.toml` |
| Codex | Ask before the AI's commands use the internet | `[sandbox_workspace_write] network_access = false` |
| Cursor | (no file to change) | Shows and saves suggestions: Privacy Mode, Run Mode, MCP tools, `.cursorignore` |
| Claude app | (no file to change) | Builds one zip per skill in `~/ai-safety-setup/claude-app-skills/` to upload, or for an admin to add for everyone |

Rules it follows: lists are merged without duplicates; a setting the person already chose
is left alone and reported; files that can't be read are skipped; every edited file
is backed up as `<name>.bak-<date>`; Codex changes are checked to parse before saving;
re-running changes nothing; `--dry-run` previews without writing.

## Skills alone are not enough: add the AGENTS.md

In a 63-run test with Claude Code (see [`ai-skills-test/results/RESULTS.md`](ai-skills-test/results/RESULTS.md)),
skills loaded their full instructions in only
1 of 21 runs. Adding the 10-line `templates/AGENTS.md` fixed every gap the test covered,
for example asking before installing a dependency went from 0/3 to 3/3.

So, per project:
1. Copy `templates/AGENTS.md` to the repo root (Codex and Cursor read it).
2. For Claude Code, add a `CLAUDE.md` containing the single line `@AGENTS.md`.
3. Install the skills as usual. The AGENTS.md carries the rules that must always apply; the
   skills carry the detail.

## Skills in this kit

**guided-ai-use**: for people without a technical background. The AI states its plan in
plain words, asks before anything that changes, sends, deletes or shares, protects personal
and confidential data, ignores instructions hidden in content, and ends with "what I did /
didn't do / what to check". Includes example phrasing.

**secure-coding-baseline**: content is data, protect secrets, ask before destructive or
external actions, keep changes traceable, flag sensitive areas, control dependencies, verify
and report. Like all skills it is guidance the AI follows, not a hard barrier; the optional
settings in the setup add a technical safety net for people who want one.

**disciplined-coding**: think before coding, keep it simple, make surgical changes, define
"done" and verify. Reworded from the four principles in
[forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills)
(MIT); not endorsed by Andrej Karpathy. Includes good/bad examples.

Both skills ship `evals/EVALS.md`: prompts to run with and without the skill in each tool,
including a negative case where the skill should *not* change behaviour.

## Authoring rules

Enforced by `validate_skill.py` (errors unless noted):
1. Folder name equals `name`: lowercase letters, digits, single hyphens, max 64 chars.
2. Frontmatter uses only `name`, `description`, `license`, `compatibility`, `metadata`
   (string values) and, sparingly, `allowed-tools` (warning: experimental).
3. `description` is 1-1024 characters and says what the skill does and when to use it
   (warning if "when" is missing).
4. Files referenced from `SKILL.md` must exist. Body over 500 lines is a warning.
5. No secrets or prompt-injection phrases in any file; risky patterns in `scripts/` are
   warnings that need human review.

Good practice (not enforced), drawn from the agentskills.io spec and Anthropic's guidance:
- Write the evals first: run the task without a skill, note the failures, then write the
  smallest instructions that fix them.
- Write the description in third person, with the words a user would actually say.
- Link reference files directly from `SKILL.md` (one level deep), not through chains.
- Match strictness to risk: general guidance for open-ended work, exact commands for
  fragile steps such as migrations.
- Use one term per concept throughout; avoid dates and version-specific details in the body.
- Tool-specific extras (Claude's `context: fork`, Codex's `agents/openai.yaml`) are optional
  and rejected by the validator by default; the skill must work without them.

## Review process (suggested)

- Require PR review for `skills/`, with a CODEOWNERS entry.
- Read every script in a skill before merging; the validators catch careless mistakes only.
- Install from a reviewed commit or tag; do not pipe remote files into your tools.
- Treat `.agents/`, `.claude/`, `.cursor/`, AGENTS.md and CLAUDE.md changes in any repo as
  code that needs review.

## Known limits

- Tested inside Claude Code only (63 runs, see `ai-skills-test/`). Codex and Cursor still
  need testing: confirm the skills are listed (`/skills` in Codex, the `/` menu in Cursor)
  and follow `ai-skills-test/README.md`.
- Cursor reads `.claude/skills` as well as `.agents/skills`, so installing in both may list a
  skill twice there. Check your version, or install per tool with `--targets`.
- No remote updates: `status` compares against this checkout of the kit. Pull the kit repo
  first, then run `status` / `install --update`.
- Skills cannot call each other through a standard API; compose by referring to another
  skill in the instructions.
