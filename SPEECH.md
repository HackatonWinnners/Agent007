# 5-Minute Speech — Needle Agent

*Read at ~140 words/min. Total ~650 words = ~4 min 40 s, leaves room for breath, pauses, and one question.*

---

## (0:00 — 0:30) hook + scores

Hi, we're team HackatonWinners. Four of us — Lap, Malachi, Konstantin, SteDP.

Our final scores: **79 out of 150 on public tests, 31 out of 100 on hidden.**

But the score isn't the project. **The agent is the project.** And our agent
made **1187 commits** between the 19:45 checkpoint and submission. Every
single one is one decision it made on its own. That's what we want to show
you.

## (0:30 — 1:30) architecture in one breath

We built a TypeScript-Bun agent inspired by the leaked Claude Code source.

It has nine tools — read, write, edit, bash, glob, grep, run_tests,
load_skill, and spawn_subagent. The `edit` tool enforces read-before-edit
and exact-match guards we lifted from Claude Code's source — that one
invariant killed an entire class of silent overwrites.

A three-tier model router with 429 cooldown and automatic failover.

A pretty terminal UI — banners, colored tool calls, iteration boxes.
A watchdog that restarts the agent when it dies and *restores the best
`knit.py` from git history* whenever the model regresses.

And twelve skills — ten generic, two knitting-specific that we wrote when
we realized the model needed a stitch-math table and an error-format
schema.

## (1:30 — 2:30) the journey

The hidden task was a Knitting Compiler — Python CLI, parse a DSL,
expand repeats, simulate stitch counts, emit one deterministic JSON.

At 20:30 we had 3 out of 150. At 22:16, basic parsing was working — 51.
At midnight, cloud peaked at 76 — then a single bad edit regressed us
back to 3. We restored from git history. By 9:54 this morning, Cerebras's
free-tier Qwen3-235B brought us to 77, and at 10:20 we hit our peak: 79.

In between, the agent burned through 906 logged decisions, 808 Cerebras
rate-limit cooldowns, 621 "thinking-without-action" nudges, 199 context
auto-compactions, 23 watchdog restarts, and 4 events where every single
cloud provider was 429-ing simultaneously. The loop kept going through
all of it.

## (2:30 — 3:30) hidden tests, honest

Hidden was 31 out of 100. Lower than public, and we know exactly why.

`boundary_stress_valid`: 14 out of 15. The math holds at scale.

`compositional_valid_patterns`: 6 out of 30. **All twenty-four failures
look identical: "expected N, got N plus 1."** A systematic off-by-one
in one stitch operation. One line of code in `knit.py`. If the agent
had pointed itself at that one cluster, it's plus-twenty-four hidden
points in five minutes.

`edge_policy` and `interaction_effect_invalid_patterns`: zero and zero.
Same root cause as public level five and six — the error-emission
pipeline never converged on the canonical `{type, code, line, row}`
schema. Another 35 points sitting on the table.

The failures aren't random. They're identifiable. With one more grind
window we close them.

## (3:30 — 4:20) what worked, what we'd change

What worked: per-iteration auto-commit made git log a play-by-play.
Claude Code's edit invariants stopped silent overwrites.
Three-tier failover kept the loop alive through 808 cooldowns.
The watchdog *restored the best solution from history* twice when
the model overwrote it with garbage.

What we'd change: build a `verify_score` tool that refuses `submit_done`
when score is too low; pull the high-water-mark snapshot logic
**into** the agent loop instead of an external bash watchdog; and write
the knitting-domain skills earlier instead of at 10am.

## (4:20 — 5:00) close

We didn't win on score. We won on process discipline.

The agent restarted itself twenty-three times. It compacted its own
context 199 times. It noticed itself in a loop eleven times and pruned.
It survived every cloud provider failing at the same time and kept
iterating. And it never lied — every intervention is timestamped in
the log.

The repo is *github dot com slash Hackat-on-Winners slash Agent zero zero seven*.
The agent is the project.

Thank you.
