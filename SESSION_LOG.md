# modelwatch, session log

Most recent first, one paragraph per session.

2026-09-22 (Step 1 build session): Pinned Inspect AI 0.3.266 from the installed package and ran `uv sync`; built the hello harness, dated roster, CLI, flatten store, and fixture test. The final run `20260922T153416+0200` evaluated the Anthropic direct snapshot and the OpenRouter Qwen snapshot with Alibaba pinned, then flattened six rows into `results\\results.ndjson` and `results\\results.sqlite`. `uv run pytest` passed 2 tests and `uv run modelwatch selftest` passed with 6 rows. Anthropic required the configured ZND workspace header; the Anthropic effort request was omitted because this dated snapshot rejects that parameter. Tagging remains a manual step.

2026-09-22 (hub Cowork session, Fable 5.1): project folder created from the approved proposal.
Written: AGENTS.md, CLAUDE.md pointer, README, DEADLINES, STATUS, 00_context\brief.md,
02_roadmap\roadmap.md, 2026-09-22_v0.1_spec.md, 2026-09-22_v0.1_session_prompts.md,
03_logs\decisions.md, config examples, 04_assets hub brief. No code. Git init and first commit
are Wilco's.
