# Pre-merge checklist for AI-assisted changes

Use this when reviewing a change that an agent produced.

## Scope
- [ ] Every changed file traces to the request; no drive-by refactors.
- [ ] No edits to CI/CD, permission, auth, infra or lockfiles unless requested.
- [ ] No tests skipped, lint rules disabled, or validation removed.

## Secrets and data
- [ ] No credentials, tokens, keys or real customer data in code, fixtures or logs.
- [ ] No new outbound calls to services the project does not already use.

## Dependencies
- [ ] New dependencies were approved, pinned and license-checked.
- [ ] Lockfile changes match the package manifest changes.

## Instruction files and skills
- [ ] Changes to AGENTS.md, CLAUDE.md, `.cursor/rules`, `.claude/`, `.agents/` or skill
      folders were reviewed by a human.
- [ ] Skill scripts were read, not just run.

## Evidence
- [ ] The agent's summary states what was verified and what was not.
- [ ] The relevant tests or checks were run and pass.
