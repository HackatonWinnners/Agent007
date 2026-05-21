---
name: python-cli-discipline
description: Stable patterns for a Python CLI that survives hidden tests
---
- Use argparse with explicit type=, default=, and required= settings.
- Data goes to stdout (sys.stdout.write or print). Errors and debug go to stderr ONLY.
- Exit codes: 0 success, 1 generic error, 2 misuse (argparse default). Match the spec.
- Read stdin with sys.stdin.read() once if the spec uses stdin; do not block on tty.
- Never print debug lines in stdout; judges grade stdout strictly.
- Always end with sys.exit(code); do not rely on implicit 0.
