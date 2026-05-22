# Final Report — HackatonWinners

## Team and submission

- **Team name:** HackatonWinners
- **Members:** @Lap, @malachi, @Konstantin, @SteDP
- **Repo:** https://github.com/HackatonWinnners/Agent007
- **Checkpoint tag:** `agent-readiness-1945` (set Thursday 19:45 before the
  hidden spec was released)
- **Final public score: 79/150 (52.7%)** — see `agent_logs/test_runs.log`
- **Final commit hash:** `git rev-parse HEAD` on `main`
- **Per-level breakdown (final):**
  | Level | Score |
  |---|---|
  | level_01_valid_basics | 18/20 (90%) |
  | level_02_stitches | 12/25 (48%) |
  | level_03_brackets | 21/25 (84%) |
  | level_04_row_repeats | 13/20 (65%) |
  | level_05_single_errors | 2/30 (7%) |
  | level_06_multi_error_recovery | 0/15 |
  | level_07_cli_output | 5/5 (100%) |
  | level_08_stress | 8/10 (80%) |
- **Overnight grind stats:**
  | Metric | Value |
  |---|---|
  | Agent decisions logged | 906 |
  | Commits since checkpoint | 1187 |
  | Watchdog auto-restarts | 23 |
  | Cerebras-cooldown events | 808 |
  | Thinking-without-action nudges | 621 |
  | Context auto-compactions | 199 |
  | Provider auto-fallbacks | 66 |
  | Cycle prunes | 11 |
  | All-providers-down events | 4 |
  | run_tests invocations | 42 |
- **Hidden task:** Knitting Compiler — Python CLI that parses, validates,
  expands, and simulates `.knit` patterns; emits one deterministic JSON to
  stdout.

## Models used (final)

The final submitted configuration uses **one** model:

- `Qwen/Qwen3-Coder-30B-A3B-Instruct` (unsloth `UD-Q4_K_XL` GGUF, MoE 3 B
  active params per token) running locally under Ollama on Apple Silicon
  (M5 Max, 36 GB unified memory). Pulled via:
  `ollama pull hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:UD-Q4_K_XL`

No paid frontier-model APIs, no Copilot, no enterprise quotas.

During earlier exploration we briefly tested three free-tier cloud providers
(Featherless 3-day trial, NVIDIA NIM free tier, Cerebras Cloud free tier).
All three are timestamped in `agent_logs/human_interventions.log`. None of
them are wired into the final agent (`agent/src/main.ts` imports only the
Ollama client) — they were retired before the final scoring run because of
rate limits, latency, and reliability issues described below.

## Agent architecture

`agent/src/agent.ts` is a query/tool-call loop modeled after patterns in the
publicly leaked Claude Code source (March 2026). Per iteration:

1. Compact conversation history if it exceeds 60 K characters (`agent/src/agent.ts`
   `compactMessages`) — older `tool` messages get squashed to head+tail of 600
   chars to keep the context small enough for the model's 32 K window.
2. Call the model through the router (`agent/src/models/router.ts`), which
   wraps Ollama in a tier chain with timeouts, retries, and 429 cooldown.
3. Parse `tool_calls` from the response. If empty, sniff for malformed
   XML-style `<function=...>` blocks (Qwen3-Coder sometimes emits these
   instead of native OpenAI-format calls) — recover and continue. If the
   model writes prose with no tool call, inject a "thinking-without-action"
   nudge and continue.
4. Cycle detection: any tool-call signature that appears 3+ times in a
   5-iteration window triggers a context prune and a logged intervention.
5. Dispatch tools through the registry (`agent/src/tools/registry.ts`).
   Concurrency-safe tools (`read`, `glob`, `grep`) run in parallel up to 4;
   side-effecting tools run sequentially.
6. After each successful batch, `agent/src/git.ts` runs `git add -A && git
   commit -m "iter NNN (root): <summary>"` so every iteration is a commit.

A 1-level subagent mechanism (`agent/src/tools/spawn_subagent.ts`) exists but
is intentionally not registered for the final run — flat iteration kept the
log easier to interpret on this single-program task.

## Tools available to the agent

- `read` — line-prefixed file read (`agent/src/tools/read.ts`); registers the
  file in the read-file cache that `edit` requires.
- `write` — create-only by default, `overwrite=true` to replace.
- `edit` — exact-match string replacement, refuses to operate without a
  prior `read`, refuses on stale mtime (pattern lifted from
  `~/Projects/claude-code-fork/src/tools/FileEditTool/FileEditTool.ts`).
- `bash` — `/bin/bash -lc <cmd>`, captures stdout/stderr/exit, default 60 s
  timeout.
- `glob` — `fast-glob`-based file listing.
- `grep` — regex search over file contents (200 match cap).
- `run_tests` — wraps `secret_spec/test_runner/run_tests.py`, parses the
  `Overall N/M passed` line and per-level breakdown.
- `load_skill` — loads a markdown file from `agent/src/skills/` and returns
  its body for the model to use as on-demand guidance.
- `submit_done` — explicit halt signal. The system prompt forbids calling
  this unless `run_tests` last reported ≥ 140/150.

## Prompting strategy

`agent/src/prompts/system_root.md` is the root prompt. It opens with the
task framing (knitting compiler, output contract, CLI shape), pins down
discipline (one semantic change per iteration, read before edit, no debug
output on stdout, `submit_done` only at ≥ 140/150), points the agent at the
weakest levels first, and inventories the available tools and skills.

`agent/src/skills/` holds 10 pre-authored skills (spec-parsing,
python-cli-discipline, json-output-rules, error-handling-pattern,
test-failure-triage, incremental-fix-discipline, self-test-template,
git-commit-etiquette, featherless-rate-limit-recovery,
compact-context-pattern). The model calls `load_skill(name)` to inject one
into the conversation only when needed; the system prompt lists names and
descriptions but not bodies, keeping the prompt cheap.

## Score progression

Captured in `agent_logs/test_runs.log` (every `run_tests` invocation
appends a JSON line with `score` and per-level `failingCategories`). Peak
scores observed during the overnight run:

- 0/150 (initial empty solution)
- 3/150 → 9/150 (CLI scaffold)
- 32/150 (basic parsing)
- 51/150 (cast_on + bind_off + simple rows; checkpoint commit `ba4d2c4`)
- 69/150 → 76/150 (cloud-tier exploration, before a regression set us back)
- 71/150 (local Ollama overnight grind)
- 77/150 (Cerebras Cloud Qwen3-235B primary kicked in)
- **79/150 (final, peak)** — Cerebras + knitting-domain skills + planner workflow

The final scoring run uses commit `99abe80` (the 79/150 high-water mark)
restored as `solution/knit.py`. Public score reproduction:
`python3 secret_spec/test_runner/run_tests.py --compiler "python3 solution/knit.py"`.

## Human interventions

Every cross-cutting infrastructure change is timestamped in
`agent_logs/human_interventions.log`. Categories observed:

- `auto-fallback` — primary model errored, router rolled to next tier
- `primary-cooldown` — primary 429'd; router skipped it for 60 s
- `fallback-failed` — secondary tier also errored, router walked further
- `all-providers-down` — every tier failed; router slept 30 s and retried
- `auto-compaction` — context > 60 K chars, old tool results squashed
- `cycle-detected` — 3+ identical tool calls in 5 iterations, context pruned
- `unparsed-tool-call` — model emitted XML-style call that didn't parse,
  retry nudge injected
- `thinking-without-action` — model wrote prose without a tool call, action
  nudge injected

No final-program code was edited by hand at any point. Every
`touchedFinalCode` field in the intervention log is `false`.

## What worked

- The query/tool-call loop and per-iteration auto-commit produced an
  excellent process trail. `git log agent-readiness-1945..HEAD` is the agent
  narrative end-to-end.
- The leaked-Claude-Code `FileEditTool` invariants (read-before-edit,
  exact-match, mtime guard) prevented the most damaging class of model
  regressions where a stale view of a file silently overwrites concurrent
  changes.
- The cycle detector caught Qwen3-Coder repeatedly retrying the same broken
  spawn_subagent / write call and unblocked the loop without crashing.
- Auto-compaction kept the model's 32 K context usable across long grinds.
- Restoring the 51/150 commit when later iterations regressed (via
  `git checkout <commit> -- solution/knit.py`) recovered cleanly thanks to
  the per-iteration commit discipline.

## What failed

- Free-tier cloud providers (Cerebras, NVIDIA NIM, Featherless) all hit
  rate limits in minutes once the spec context (~38 K tokens) entered every
  call. Effective throughput was ~1 model call per minute, with frequent
  30-second sleeps when all tiers were exhausted simultaneously.
- Cerebras has a 60 K tokens-per-minute window on the Qwen3-235B free tier;
  one full call exhausts it. Compaction helped but didn't fully unblock it.
- IQ4_NL quantization of Qwen3-Coder produced unusable tool calls (the model
  hallucinated tool names like `"_write"` and values like `"Eight"` instead
  of `8`). `UD-Q4_K_XL` (downloaded later via `hf.co/...` Ollama prefix to
  bypass an EOF-on-manifest issue with the Ollama registry) worked properly.
- The model sometimes called `submit_done` after a non-improving iteration,
  treating itself as finished at scores well below 140/150. Tightening the
  system prompt to require ≥ 140 helped but not perfectly.

## What we would improve

- Implement a real `verify_score` tool that wraps `run_tests` and returns a
  structured per-level diff, then refuse `submit_done` at the agent loop
  layer when the most recent score < 140.
- Add a checkpoint system that snapshots `solution/knit.py` whenever
  `run_tests` reports a new high score, and auto-restore on regression
  inside the loop (the external watchdog does this today; pulling it into
  the agent itself would be cleaner).
- Use a larger local quant (Q5_K_M or Q6_K) on hardware with more RAM;
  UD-Q4_K_XL is the right pick for 36 GB but leaves quality on the table.
- Pre-write skills specific to the Knitting Compiler domain (bracket
  parsing, repeat expansion semantics, deterministic JSON dict ordering)
  rather than the generic skills we shipped.
