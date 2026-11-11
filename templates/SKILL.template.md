---
name: my-skill-name
description: One or two sentences, third person: what this skill does, then when to use it, including trigger terms the user would say.
license: MIT
compatibility: Optional. Environment needs, for example "Requires git and Python 3.10+".
metadata:
  owner: team-or-person
  version: "0.1.0"
---

# Title

Short statement of purpose.

## Steps
1. First step.
2. Second step, with a verification: how to confirm it worked.

## Notes
- Keep this file under 500 lines. Move long material to `references/`.
- Reference helper files with relative paths, for example `references/REFERENCE.md`
  or `scripts/check.sh`.

<!--
Portability rules for this kit:
- Folder name must equal `name` (lowercase letters, digits, single hyphens; max 64 chars).
- Use only these frontmatter fields: name, description, license, compatibility,
  metadata (string values only), allowed-tools (experimental, avoid unless needed).
- Tool-specific features (Claude `context: fork`, `disable-model-invocation`, Codex
  `agents/openai.yaml`) are optional extras. Keep the skill useful without them.
-->
