---
name: self-test-template
description: Spec-derived pytest cases that harden the solution
---
For each rule R in the spec, write tests in solution/self_tests/test_R.py:
- positive case (happy path)
- boundary case (empty or max-size)
- malformed case (expect specific exit code and stderr substring)
- unicode or whitespace edge case
Use subprocess.run(['python3', 'solution/main.py', ...], capture_output=True) and assert on stdout bytes, stderr substring, returncode.
