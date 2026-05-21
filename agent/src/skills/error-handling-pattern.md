---
name: error-handling-pattern
description: When to raise, when to print and exit
---
- Wrap main() in a top-level try/except Exception as e: print('error:', e, file=sys.stderr); sys.exit(1).
- For spec-defined error categories, raise a custom ValueError subclass with the spec's message text, then map to the spec's exit code.
- Do not swallow exceptions inside helpers; let them bubble to main().
- Never use bare except; catch the narrowest class possible.
