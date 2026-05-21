# Needle Agent — Hackathon Submission

## Team
- name: TBD-before-13:00-thursday
- members: ...
- repo visibility: ...

## Final command (placeholder, agent fills post-reveal)
`python3 solution/main.py <args from spec>`

## Setup
```bash
./setup.sh
cp .env.example .env  # paste FEATHERLESS_API_KEY
```

## Run the agent
```bash
cd agent && bun install && bun run src/main.ts --spec ../secret_spec/SECRET_SPEC.md
```

## Agent overview
TypeScript/Bun coordinator with a query/tool-call loop, 1-level subagents
(planner / implementer / tester / failure_analyst / self_test_writer), an
on-demand skill loader, and structured logs. Primary model: Featherless
Qwen3-Coder-480B; fallback: local Ollama Qwen2.5-Coder-7B.

## Checkpoint
Git tag: `agent-readiness-1945`

## Public test run
`python3 secret_spec/test_runner/run_tests.py --program "python3 solution/main.py" --suite public`

## Known limitations
(filled at submission)
