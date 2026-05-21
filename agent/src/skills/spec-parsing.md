---
name: spec-parsing
description: Extract CLI behavior, IO format, and error rules from a hidden spec
---
When reading the hidden spec, produce a written list with these sections in order:
1. Required command and arguments (literal flag names, types, defaults).
2. Stdin/stdout/stderr contract (data on stdout, errors on stderr; exact format).
3. Exit codes table (code -> meaning).
4. Input format details (delimiters, encoding, whitespace handling).
5. Output format details (sort order, separators, trailing newline, JSON shape if any).
6. Error rules (which inputs are rejected, what message/code).
7. Edge cases (empty input, max size, malformed bytes, unicode).
After writing this list, do NOT start coding. Call load_skill('incremental-fix-discipline') and load_skill('python-cli-discipline') first.
