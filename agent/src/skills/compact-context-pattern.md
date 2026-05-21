---
name: compact-context-pattern
description: When and how to compress conversation history
---
Compaction triggers (root only):
- prompt token estimate > 80,000
- iteration > 80
- 3 tool-result messages in a row > 8 KiB each
Compaction action:
- Keep the system prompt, the original spec read, the last 4 tool messages, and a summary of everything older.
- The summary is a 200-word recap of: solution state, latest score, failing categories, last 3 decisions.
Subagents do not compact; they have their own short windows.
