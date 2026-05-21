---
name: git-commit-etiquette
description: One semantic change per commit; clear messages
---
- Stage and commit per successful iteration (auto by the loop). Manual commit message format: "iter NNN (agentId): summary".
- Do not add Co-Authored-By lines unless asked.
- Never amend committed iterations; keep history append-only for judges.
- If reverting, use git revert <hash> (preserve history) for intentional reverts; only use git reset --hard inside the iteration loop where the loop expects it.
