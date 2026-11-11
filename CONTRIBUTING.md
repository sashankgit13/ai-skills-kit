# Adding or changing a skill

Every new skill, and every change to an existing one, goes through a team review before it
reaches anyone's AI tools. Nothing is shared until at least one teammate has read it.

## How it works

```
Idea  ->  Draft  ->  Pull request  ->  Checks + review  ->  Merge  ->  Team updates
```

1. **Idea.** Anyone can suggest a skill, no coding needed (see below).
2. **Draft.** Someone writes the skill from the template and tests it.
3. **Pull request.** The draft is proposed as a change to this repo.
4. **Checks and review.** Automatic checks run, and at least one teammate reviews it using
   the checklist in the pull request.
5. **Merge.** Once approved, it becomes part of the kit and appears in
   [SKILLS.md](SKILLS.md) automatically.
6. **Team updates.** People re-run the setup, or a developer runs
   `python3 tools/install.py install --update`, to get the new or changed skill.

## Suggesting a skill (no coding needed)

Open a new issue and choose **Propose a skill**: go to the **Issues** tab, click
**New issue**, and fill in the short form. Good candidates:

- instructions you keep repeating to the AI;
- a mistake the AI keeps making;
- a task where the team wants everyone to work the same way.

## Writing a skill

1. **Start from the template.** Copy `templates/SKILL.template.md` to
   `skills/<skill-name>/SKILL.md`. The folder name must match the `name` field: lowercase
   letters, numbers and hyphens.
2. **Write the description first.** One or two sentences: what the skill does, then
   "Use when..." with the words people actually say. This is how the AI decides to use it.
3. **Keep it short.** Under 500 lines; put long examples in `references/`. Each `## `
   heading in the body becomes a rule in the catalog, so name headings as rules
   ("Ask before deleting files", not "Notes").
4. **Add tests.** Write `evals/EVALS.md` with a few realistic prompts and what a pass looks
   like, including one prompt where the skill should *not* change anything.
5. **Try it.** Run your prompts with and without the skill in at least one AI tool. For
   coding skills, `ai-skills-test/run_evals.py` can do this automatically for Claude Code.
6. **Run the checks locally:**
   ```bash
   python3 tools/validate_skill.py skills/
   python3 tools/build_catalog.py        # updates SKILLS.md
   ```
7. **Open a pull request** on a new branch. Fill in the checklist.

**Changing an existing skill:** bump `metadata.version` (for example `0.1.0` to `0.2.0`) so
people's installed copies show as outdated, and say what changed in the pull request.

**Removing a skill:** delete its folder, rebuild the catalog, and say in the pull request
why. People remove it with `python3 tools/install.py uninstall --skill <name>`.

## Reviewing a skill

Reviewers use the checklist in the pull request. The main questions:

- **Is it needed?** Does it solve a real, repeated problem, without duplicating a skill we
  already have?
- **Is it clear?** Would someone new to AI understand what it makes the AI do?
- **Is it safe?** No secrets, no hidden instructions, and every script read line by line.
  Scripts get the most scrutiny: they run on people's computers.
- **Was it tested?** The evals were run, and the results are described in the pull request.
- **Does it conflict** with another skill or with `templates/AGENTS.md`?

## Changing the always-on rules (AGENTS.md)

`templates/AGENTS.md` is read on every task, so changes need a higher bar:

- **two** approving reviewers;
- keep it short (the tested version is 10 lines);
- re-run the test harness (`ai-skills-test/run_evals.py`) and include the before and after
  results in the pull request.

## Automatic checks

Every pull request runs these, and a failing check blocks the merge (once required-review
rules are turned on, see below):

- **Skill validator:** format, portability, and scans for secrets, hidden instructions and
  risky scripts.
- **Official spec validator** (`skills-ref` from agentskills.io).
- **Catalog check:** `SKILLS.md` must match the skills. If it fails, run
  `python3 tools/build_catalog.py` and commit the result.

## For the repo owner: require reviews

To make sure nothing merges without review, turn on branch protection once:
**Settings > Branches > Add rule** for `main`, then tick **Require a pull request before
merging** (1 approval), **Require review from Code Owners**, and **Require status checks
to pass** (select "Validate skills"). Add reviewers to `.github/CODEOWNERS`.
