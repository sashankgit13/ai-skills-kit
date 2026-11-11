# Evaluation scenarios

For humans testing the skill. Agents do not need to read this file.

Method: run each prompt in a small sample repo twice, once without the skill installed and
once with it, in each tool you support (Claude Code, Codex, Cursor). Record pass/fail per
criterion. Keep the skill only if it improves results and does not trigger where it should not.

| # | Prompt | Pass criteria |
|---|---|---|
| 1 | "Make the submit button orange." (repo has a shared theme file) | Only the button's style changes; no theme-wide or unrelated edits |
| 2 | "Fix the bug where totals are wrong." (vague; two plausible causes) | Asks which case, or states an assumption, before editing |
| 3 | "Add input validation to `create_user`." | Adds tests for invalid inputs first; tests fail then pass; reports what was run |
| 4 | "Add a retry to the HTTP call in `fetch_rates`." | Small diff in that function; no new config system or retry framework |
| 5 | "Rename `calc` to `calculate_total` in billing.py." (file has unused helpers) | Renames only; mentions unused helpers without deleting them |
| 6 | Negative: "What does `paginate()` do?" | Explains; makes no edits and does not produce a plan/verify ritual |

Track over time: diff size (lines changed), number of files touched, whether clarifying
questions were asked, and whether a verification step was reported.
