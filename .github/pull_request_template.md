## What this changes

<!-- New skill, change to a skill, or change to templates/AGENTS.md. One or two sentences. -->

**Skill(s):**
**Linked idea / issue:**

## How it was tested

<!-- Which AI tool(s), which prompts from evals/EVALS.md, and what happened with and without the skill. -->

## Author checklist

- [ ] Folder name matches `name`; description says what it does **and** "Use when..."
- [ ] `evals/EVALS.md` included, with at least one prompt where the skill should not change anything
- [ ] Tested with and without the skill in at least one AI tool (results above)
- [ ] `python3 tools/validate_skill.py skills/` passes
- [ ] `python3 tools/build_catalog.py` run and `SKILLS.md` committed
- [ ] `metadata.version` bumped (changes to an existing skill)
- [ ] No real secrets, customer data or personal data anywhere, including examples

## Reviewer checklist

- [ ] Solves a real, repeated problem; doesn't duplicate an existing skill
- [ ] Clear to someone new to AI; rules are short and specific
- [ ] Every script read line by line (nothing downloads, deletes or sends data unexpectedly)
- [ ] No hidden instructions or anything that tells the AI to keep things from the user
- [ ] Doesn't conflict with other skills or `templates/AGENTS.md`
- [ ] Changes to `templates/AGENTS.md`: two approvals and before/after test results
