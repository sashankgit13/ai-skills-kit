---
name: disciplined-coding
description: Keeps AI-written code changes small, simple and verified. Use when writing, fixing, refactoring or reviewing code, especially for bug fixes, new features, ambiguous requests, or any change that touches existing files.
license: MIT
compatibility: Any agent that supports the Agent Skills format (Claude Code, Codex, Cursor). No extra tools needed.
metadata:
  owner: platform-ai
  version: "0.1.0"
  based-on: "forrestchang/andrej-karpathy-skills (MIT), reworded"
---

# Disciplined coding

Four habits that prevent the most common agent mistakes: guessing silently, overbuilding,
editing unrelated code, and stopping without proof. They favour care over speed. For a
one-line fix or a typo, use judgment and skip the ceremony.

## 1. Think before coding
- State your assumptions in one or two lines before you start.
- If the request can be read more than one way, list the readings and ask. Do not pick one
  silently.
- If something is unclear or contradicts the code, stop and name what is confusing.
- If a simpler approach than the one requested exists, say so before building.

## 2. Keep it simple
- Write the least code that meets the request. No features, options or configuration
  nobody asked for.
- No abstraction for code used once. No error handling for cases that cannot happen.
- Before finishing, ask: would a senior engineer call this overcomplicated? If yes,
  simplify.

## 3. Make surgical changes
- Touch only what the task needs. Every changed line should trace to the request.
- Match the existing style, naming and structure, even if you would write it differently.
- Do not reformat, rename, reorder or "improve" nearby code, comments or docs.
- Remove imports, variables and functions that *your* change made unused. Leave
  pre-existing dead code alone and mention it instead.

## 4. Define done, then verify
Turn the request into something checkable before you start:

| Request | Checkable goal |
|---|---|
| Fix the bug | Write a test that reproduces it, then make it pass |
| Add validation | Write tests for the invalid inputs, then make them pass |
| Refactor X | Tests pass before and after, behaviour unchanged |

For multi-step work, write a short plan where each step has its check:

```
1. <step> -> verify: <command or observable result>
2. <step> -> verify: <command or observable result>
```

Run the checks. In your final message, say what you verified, what you could not verify,
and anything you noticed but deliberately left alone.

For worked examples of each habit, see `references/EXAMPLES.md`.
