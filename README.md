# Needle Agent — HackatonWinners

42 Berlin × Needle Agent Hackathon submission.

A TypeScript/Bun coding agent that reads the hidden spec, builds the Knitting
Compiler in Python, runs the public test suite, and iterates fixes until it
either exhausts iterations or the score crosses 140/150.

## Team

- **Name:** HackatonWinners
- **Members:** @Lap @malachi @Konstantin @SteDP
- **Repo:** https://github.com/HackatonWinnners/Agent007
- **Visibility:** public

## Final command (Knitting Compiler)

```bash
python3 solution/knit.py compile <input.knit>
```

## Setup

```bash
./setup.sh                    # installs Bun and runs `cd agent && bun install`
brew install --cask ollama    # local LLM runtime
open -a Ollama                # start the daemon
ollama pull hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:UD-Q4_K_XL
cp .env.example .env          # defaults are fine for local Ollama
```

Requirements: macOS Apple Silicon with ≥ 20 GB free RAM (32 GB+ recommended),
Bun ≥ 1.3, Python 3.11+, Ollama ≥ 0.24.

## Run the agent

```bash
cd agent
bun run src/main.ts --spec ../secret_spec/SECRET_SPEC.md --repo-root ..
```

The agent reads the spec, edits `solution/knit.py`, runs the public test
runner, and iterates. Every iteration auto-commits, so `git log` is a
play-by-play.

## Public test run (judges, reproduce final score)

```bash
python3 secret_spec/test_runner/run_tests.py --compiler "python3 solution/knit.py"
```

## Agent overview

Single-file orchestrator in `agent/src/main.ts` wires:

- **Model:** local Ollama serving `Qwen3-Coder-30B-A3B-Instruct` (unsloth's
  `UD-Q4_K_XL` quantization). MoE with 3 B active parameters per token, runs
  at ~80 tok/s on M5 Max. Zero network, zero rate limits.
- **Tools:** `read`, `write`, `edit`, `bash`, `glob`, `grep`, `run_tests`,
  `load_skill`, `submit_done` — each a self-contained module under
  `agent/src/tools/`. `edit` enforces read-before-edit and exact-match
  semantics (pattern lifted from the leaked Claude Code source).
- **Loop:** `agent/src/agent.ts` — read spec → emit tool calls → execute →
  feed results back → repeat. Includes cycle detection (3+ identical tool
  calls in a 5-window prunes context), context compaction (>60 K char
  history triggers head+tail squash of old tool results), and recovery from
  XML-style tool calls (Qwen sometimes emits `<function=...>` instead of
  native OpenAI-format calls).
- **UI:** pretty colored terminal output (`agent/src/ui.ts`) — visible when
  attached to a TTY or with `AGENT_FORCE_UI=1`.
- **Logging:** structured JSON-tail lines in `agent_logs/`. Every iteration,
  every tool call, every fallback, every cycle prune, every recovery.

## Checkpoint

Git tag `agent-readiness-1945` marks the agent state at the Thursday 19:45
checkpoint, before the hidden spec was released. `git log agent-readiness-1945..HEAD`
shows the entire post-reveal evolution.

## Public score

Best score during the run is captured in `agent_logs/test_runs.log` and
`agent_logs/final_report.md`.

## Known limitations

- The agent occasionally stops mid-grind when the local model emits a long
  reasoning paragraph without a tool call. `agent/src/agent.ts` injects a
  "thinking-without-action" nudge to push it back into action, but a few
  loops still terminate early. The watchdog (`/tmp/needle_watchdog.sh`,
  external to this repo) auto-restarts the agent when this happens.
- Quantization tradeoff: `UD-Q4_K_XL` was chosen for the M5 Max 36 GB RAM
  envelope. A larger quant (Q5/Q6) or the 480 B variant would likely score
  higher, but at the cost of speed or memory.
