# 5-Minute Speech — Needle Agent

*~430 words spoken at ~140 wpm ≈ 3 min, leaves room for pauses + Q&A.*

---

## (0:00 — 0:30) hook

Team HackatonWinners — four of us.

Public: **79 out of 150.** Hidden: **31 out of 100.**

But the score isn't the project. **The agent is the project.** Between the
19:45 checkpoint and now, our agent made **1187 commits** — every single one
a decision it made on its own.

## (0:30 — 1:10) architecture

A TypeScript-Bun agent, built from scratch. Nine tools, twelve skills,
three-tier model router, watchdog supervisor.

The `edit` tool enforces read-before-edit and exact-match guards — one
invariant that killed an entire class of silent overwrites.

Cerebras Cloud's free tier (Qwen3-235B) as primary; local Ollama
(Qwen3-Coder-30B) as fallback when Cerebras hits its per-minute quota.

## (1:10 — 2:00) one full cycle — *(walk the diagram)*

Agent Loop in the center. It reads the spec once, then per iteration it
hits the Model Router, parses tool calls, dispatches through the Tool
Registry. `edit` mutates `knit.py`. `run_tests` invokes the spec test
runner and pipes the score back.

Three safety nets: a **Cycle Detector** that prunes when the model spins,
**Auto-Compaction** that squashes old tool results past 60K characters, and
a **Thinking-Nudge** that forces a tool call when the model narrates
without acting.

Everything logs to `agent_logs/`. Every iteration auto-commits. And from
outside, a **Watchdog** restarts the agent on death, restores the best
`knit.py` from git when the score regresses, and pushes every ten minutes.

## (2:00 — 2:40) the journey

Twenty thirty: three out of one fifty. Twenty-two sixteen: fifty-one.
Midnight: cloud peaked at seventy-six — then one bad edit dropped us to
three. We restored from git history. By morning, Cerebras brought us to
seventy-seven; the knitting-domain skills we wrote at ten a.m. pushed us
to **seventy-nine**.

In between: **906 decisions, 808 Cerebras cooldowns, 621 nudges, 199
compactions, 23 watchdog restarts, four total cloud-outage events.** The
loop kept going through all of it.

## (2:40 — 3:20) hidden tests, honest

Thirty-one out of one hundred. Lower than public — and we know exactly
why.

`compositional_valid_patterns`: six out of thirty. **All twenty-four
failures show the same off-by-one in one stitch operation.** One line of
code. Plus-twenty-four hidden points if the agent had pointed at it.

`edge_policy` and `interaction_effect_invalid_patterns`: zero and zero.
Same root cause as our weak public error-handling categories. Another
thirty-five points sitting on the table.

The failures aren't random. They're identifiable.

## (3:20 — 3:50) close

We didn't win on score. We won on process.

The agent restarted itself twenty-three times. It compacted its own
context one hundred and ninety-nine times. It noticed itself in a loop
eleven times and pruned. It survived every cloud provider failing
simultaneously. And every intervention is timestamped in the log.

Repo: *github dot com slash Hackat-on-Winners slash Agent zero zero
seven*.

**The agent is the project.** Thank you.
