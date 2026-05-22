# NEEDLE AGENT

## team HackatonWinners — @Lap @malachi @Konstantin @SteDP

**Public: 79/150 (52.7%) · Hidden: 31/100 (31%)**
*A self-restarting, watchdog-guarded, multi-tier coding agent that
overnight ground a knitting compiler out of nothing.*

---

## the rules of the game

- Read a hidden spec at 20:00 Thursday
- Build the program it describes
- Submit by 12:00 Friday
- Use only **free** or **local** models — no paid Claude/GPT/Copilot
- Judges grade: 40% hidden tests + 20% public + 20% process + 10% self-tests + 10% talk
- *The agent is the project. The program is just the battlefield.*

---

## what we built (before reveal)

A TypeScript/Bun coding agent inspired by the leaked Claude Code source.

- **9 tools**: `read`, `edit`, `write`, `bash`, `glob`, `grep`, `run_tests`, `load_skill`, `spawn_subagent`, `submit_done`
- **`edit` invariants from Claude Code**: read-before-edit, exact-match, mtime guard
- **query/tool-call loop** with cycle detection, auto-compaction, XML-tool-call recovery
- **Multi-tier model router** with timeout, retry, 429 cooldown, fallback chain
- **Subagent system** (planner / implementer / tester / failure_analyst / self_test_writer)
- **10 pre-written skills** + 2 knitting-domain skills (`knitting-error-format`, `knitting-stitch-math`)
- **Pretty terminal UI** with ANSI boxes (Claude Code vibe)
- **Watchdog** that restarts agent on death and restores best `knit.py` on regression

---

## the reveal (20:00)

`secret_spec/SECRET_SPEC.md` — **Knitting Compiler**, 927 lines

```bash
python3 solution/knit.py compile <file.knit>
```

Parses a knitting DSL, validates, expands repeats, simulates stitch counts row by row, emits one deterministic JSON. 150 public tests across 8 levels of difficulty.

---

## the journey

| time  | score   | what                                                |
|-------|---------|-----------------------------------------------------|
| 20:30 | 3/150   | first scaffold via Featherless Qwen3-Coder-480B     |
| 22:16 | 51/150  | basic parsing + simulation                          |
| 00:00 | 76/150  | cloud peak — then regressed by an over-eager edit   |
| 03:00 | 71/150  | local Ollama overnight grind                        |
| 09:54 | 77/150  | Cerebras Cloud Qwen3-235B back in primary           |
| 10:20 | **79/150** | knitting-domain skills + planner workflow      |

---

## the model carousel

| Tried | Verdict |
|---|---|
| DeepSeek V4-Pro (Featherless) | `tools=false` — useless |
| DeepSeek V3.2 (Featherless) | empty-args bug |
| DeepSeek V3-0324 (Featherless) | markdown instead of native tools |
| Qwen3-Coder-480B (Featherless) | slow + drops |
| Qwen3-Coder-480B (NVIDIA NIM) | rate-limited fast |
| Qwen3-235B (**Cerebras free**) | ~2000 tok/s — primary |
| Qwen3-Coder-30B UD-Q4_K_XL (local Ollama) | ~80 tok/s — fallback |
| Qwen3-Coder-30B IQ4_NL (local) | broken — invented tool names like `_write`, args like `"Eight"` |

---

## the overnight grind (in numbers)

| metric | count |
|---|---:|
| agent decisions logged | **906** |
| commits since checkpoint | **1187** |
| watchdog auto-restarts | 23 |
| Cerebras-cooldown events | 808 |
| thinking-without-action nudges | 621 |
| context auto-compactions | 199 |
| provider auto-fallbacks | 66 |
| cycle prunes | 11 |
| all-providers-down events | 4 |
| run_tests invocations | 42 |

---

## what worked

- **Per-iteration auto-commit** — `git log` is a play-by-play of the agent's thinking
- **Claude Code's edit invariants** — read-before-edit + exact-match killed an entire class of silent overwrites
- **Cycle detector** — 3+ identical tool calls in a 5-window → context prune
- **Auto-compaction** — old tool results squashed to head+tail when context > 60 KB
- **3-tier model failover** + 429 cooldown — kept the loop alive when Cerebras hit TPM
- **Watchdog with regression restore** — pulled the best `knit.py` back from commit history when the model overwrote it with garbage

---

## hidden tests — post-mortem (31/100)

| hidden category | score | diagnosis |
|---|---|---|
| boundary_stress_valid | **14/15** | large patterns work, math holds at scale |
| cli_behavior | **4/5** | CLI contract solid |
| schema_exactness_valid_outputs | 7/15 | half — JSON field shape mismatches |
| compositional_valid_patterns | 6/30 | **systematic off-by-one in stitch math** — 24/24 failures show `expected N, got N+1` |
| edge_policy | **0/10** | not detecting invalid → exit 0 when judge expects 1 |
| interaction_effect_invalid_patterns | **0/25** | same root cause as public level_05/06 — error emission shape never landed |

**Root causes (identifiable, not random):**
- One stitch op (likely `yo` / `m1` / `kfb`) produces +1 too many stitches → 24 free points
- Whole error-emission pipeline never converged on the canonical `{type, code, line, row}` schema → 35 points trapped
- One more agent grind window aimed at level_05/06 would have closed both gaps

---

## what failed

- **Free-tier rate limits** stalled us 30 min at a time when all 3 cloud providers were 429
- **IQ4_NL quantization** of Qwen3-Coder produced hallucinated tool calls — switched to **UD-Q4_K_XL**
- **Ollama registry** had EOF-on-manifest issues for `qwen3-coder:30b` — bypassed via `hf.co/unsloth/...:UD-Q4_K_XL`
- **`submit_done` premature calls** at sub-150 scores → tightened prompt to require ≥ 140
- **Level_05 (single errors) only 2/30** — knitting error JSON format was the biggest unsolved bucket

---

## what we'd improve given more time

- A **`verify_score` tool** that wraps `run_tests` and lets the loop refuse `submit_done` when score < 140
- **High-water-mark snapshots inside the agent** (today we did it via an external watchdog)
- **Bigger local quant** (Q5_K_M / Q6_K) on hardware with more RAM
- **Spec-derived self-tests** generated proactively, not just at the end
- **Per-level subagents** that own one category and don't context-pollute the rest
- **Hidden-test post-mortem loop:** if we'd had a second 4-hour window we'd point a fresh agent at the off-by-one stitch math (worth +24 hidden points) and the canonical error schema (worth +35 hidden points). The failures are systematic — not noise — and the agent is already wired to grind specific bugs.

---

## the agent is the project

```
agent-readiness-1945  ← Thursday 19:45 checkpoint (set before the spec was even open)
              │
              └─ 1187 commits ─→ HEAD  (every iteration a commit, every commit a decision)
```

Public score is the battlefield score.
The agent is what we built.

**https://github.com/HackatonWinnners/Agent007**

---

## thank you 🧶
