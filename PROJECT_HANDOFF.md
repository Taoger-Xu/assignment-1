# Project handoff

This file records durable project state for continuing the work in a new Codex
session or on another device. It intentionally contains no credentials.

## Current status

- Parts 1 and 2 are implemented.
- Part 3 source implementation is complete.
- `make test` passes: 15 tests passed and 4 Modal tests were deselected.
- `make test-chess-modal` passes: 1 test passed.
- The basic Part 3 DeepSeek chess run reached a terminal state.
- Both DeepSeek observation conditions were run and analyzed in
  `artifacts/observation-experiment.md`.
- The programmatic skill trajectory contains `invoke_skill`, followed by
  `run_python` code using `simulate_move` and one `play_move` call.

## Remaining limitation

The two GPT-OSS observation runs are missing. The configured DeepSeek-compatible
endpoint exposes only `deepseek-flash` and `deepseek-v4-pro`, not the assignment's
`openai/gpt-oss-120b`. Configure an OpenAI-compatible provider that serves that
exact model, then run:

```bash
make run-obs-gpt-oss-no-legal
make run-obs-gpt-oss-legal
```

Afterward, update `artifacts/observation-experiment.md` with the two new rows.

## Local setup on another device

```bash
git clone git@github.com:Taoger-Xu/assignment-1.git
cd assignment-1
uv sync
cp .env.example .env
```

Populate `.env` locally. Never commit `.env` or API keys. Modal authentication
must also be configured on the new machine before running billable experiments.

## Important files

- `ASSIGNMENT.md`: authoritative requirements and submission list.
- `src/assignment/agent/base.py`: shared Agent loop, skills, and compaction.
- `src/assignment/agent/code_agent.py`: coding-agent tool dispatch.
- `src/assignment/agent/chess_agent.py`: chess tool dispatch and live state.
- `src/assignment/agent/chess_tools.py`: chess HTTP and Python-sandbox helpers.
- `src/assignment/agent/tools.py`: function-tool schemas.
- `artifacts/token-usage-analysis.md`: Part 2 analysis.
- `artifacts/observation-experiment.md`: Part 3 analysis.

## Resume prompt for a new Codex chat

> Read `ASSIGNMENT.md`, `PROJECT_HANDOFF.md`, and the current Git status. Continue
> from the recorded project state without regenerating completed experiments.
> Preserve `.env` and never print credentials. First run the free tests, then
> identify whether the GPT-OSS provider is configured before starting paid runs.
