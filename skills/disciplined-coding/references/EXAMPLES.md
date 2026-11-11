# Examples

Short contrasts for each habit in SKILL.md. "Avoid" shows the failure; "Prefer" shows the fix.

## 1. Think before coding

Request: "Export the users list."

- Avoid: building a CSV exporter with filters and pagination, assuming that is what was meant.
- Prefer: "Two readings: (a) a CSV download for admins, (b) a JSON API endpoint. Which one?
  I'll assume (a) with all columns if you don't mind."

## 2. Keep it simple

Request: "Read the timeout from an environment variable."

- Avoid: a new `ConfigLoader` class with a provider interface, YAML support and caching.
- Prefer: `timeout = int(os.environ.get("APP_TIMEOUT", "30"))` where the value is used.

## 3. Make surgical changes

Request: "Fix the off-by-one error in `paginate()`."

- Avoid: fixing the bug, then also renaming variables, converting the file to f-strings,
  reordering imports and deleting an unused helper someone else wrote.
- Prefer: a two-line diff in `paginate()`, plus a note: "`old_paginate()` looks unused;
  left it in place."

## 4. Define done, then verify

Request: "The signup form accepts empty emails. Fix it."

- Avoid: adding a check and reporting "Fixed."
- Prefer:
  ```
  1. Add a test that submits an empty email -> verify: test fails on current code
  2. Add the validation -> verify: new test passes, existing signup tests still pass
  ```
  Final message: "Added test `test_signup_rejects_empty_email`; it failed before and passes
  now. Full suite passes. Did not check the mobile client, which has its own form."
