---
name: featherless-rate-limit-recovery
description: What to do on 429 or 5xx from Featherless
---
- Backoff is already automatic via the router (1s, 4s, 12s).
- After retries exhaust, the router auto-falls back to Ollama and logs an INTERVENTION. Do not try to force it back.
- If many calls are failing, reduce context size; call load_skill('compact-context-pattern').
- If the trial may have expired (401 on every call), pause and ask the driver to swap providers; this is an intervention.
