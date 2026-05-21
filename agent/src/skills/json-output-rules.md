---
name: json-output-rules
description: Deterministic JSON output that passes byte-exact comparisons
---
- json.dumps(obj, sort_keys=True, separators=(',', ':')) for compact deterministic output unless the spec requires whitespace.
- No trailing newline unless the spec mandates it.
- Floats: use round(x, N) per spec; never rely on Python's default repr.
- Numbers that are integers must serialize without a trailing decimal.
- Lists ordered as specified; if order is not specified, sort lexicographically.
