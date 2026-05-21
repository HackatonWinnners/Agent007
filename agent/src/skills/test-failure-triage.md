---
name: test-failure-triage
description: Categorize public-test failures into actionable buckets
---
For each failing test, identify one of:
- parsing: input was not read correctly.
- format: output bytes differ (whitespace, separators, trailing newline).
- logic: output structure correct but value wrong.
- exit_code: program returned a value the runner did not expect.
- crash: traceback, missing module, syntax error.
Fix one bucket at a time, starting with the bucket with the most failing tests. Re-run after every fix.
