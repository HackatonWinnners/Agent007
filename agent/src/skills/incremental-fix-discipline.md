---
name: incremental-fix-discipline
description: Small targeted patches with re-run and revert
---
- Make ONE semantic change, then run_tests.
- If the score goes up, commit (auto by the loop).
- If the score goes down or stays the same with new failures, revert via bash (git reset --hard HEAD~1) and try a different angle.
- Never bundle two unrelated fixes in one iteration; you lose the signal.
- After 3 failed attempts on the same bucket, spawn failure_analyst.
