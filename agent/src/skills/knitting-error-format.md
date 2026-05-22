---
name: knitting-error-format
description: Exact JSON shape and field names the test runner compares for invalid compiles
---
When the compiler detects an invalid pattern, exit code is 1 AND stdout must contain ONE JSON object with a non-empty `errors` array. The runner compares only these fields on each error object:

- `type` (string) — error category, e.g. "syntax", "validation", "stitch_count", "repeat"
- `code` (string) — short stable identifier, e.g. "E_UNCLOSED_BRACKET", "E_UNKNOWN_STITCH", "E_STITCH_OVERFLOW"
- `line` (integer) — 1-based physical line number in the input file. Blank lines and comments still count.
- `row` (integer | null) — 1-based row number from the pattern (null if the error isn't inside a row)
- `message` (string) — human-readable; runner only checks it's a non-empty string, NOT the exact wording.

Output skeleton for an invalid compile:

```json
{
  "pattern_name": "...",   // best-effort, may be null if header itself bad
  "cast_on": 0,
  "valid": false,
  "errors": [
    {"type": "syntax", "code": "E_UNCLOSED_BRACKET", "line": 3, "row": 1, "message": "..."},
    ...
  ],
  "expanded_rows": [],     // empty when invalid
  "final_stitch_count": 0,
  "bind_off": false
}
```

For multi-error files (level_06): KEEP PARSING after the first error. Accumulate errors in order of `line` then in encounter order. Do NOT short-circuit on first error. Each row that has a fatal error contributes one error entry; recoverable parse errors still emit row data when possible.

Reusable error codes (use these, not invented ones):
- E_UNKNOWN_STITCH, E_UNKNOWN_COMMAND, E_BAD_NUMBER, E_BAD_NAME
- E_UNCLOSED_BRACKET, E_UNEXPECTED_BRACKET, E_EMPTY_BRACKET
- E_UNCLOSED_QUOTE, E_DUPLICATE_PATTERN, E_DUPLICATE_CAST_ON
- E_MISSING_CAST_ON, E_MISSING_PATTERN_NAME
- E_STITCH_OVERFLOW, E_STITCH_UNDERFLOW, E_STITCH_COUNT_MISMATCH
- E_REPEAT_BAD_RANGE, E_REPEAT_BAD_COUNT, E_REPEAT_UNKNOWN_ROW
- E_BIND_OFF_BEFORE_ROWS, E_TRAILING_AFTER_BIND_OFF
