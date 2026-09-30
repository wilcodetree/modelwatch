# modelwatch, decisions

Newest on top, each with its why.

- 2026-09-24 Light path replaces the Inspect run path (Wilco). Standard questions run weekly
  inside Claude Code and Codex CLI by one script, answers saved as files, one judge (Claude Opus
  via `claude -p`, self-preference bias disclosed, not corrected), one curve. Why: the v0.1 full
  run of 2026-09-23 got 857 of 1,500 usable scores because of API credits, 429s and an interrupt;
  ten API keys and a Docker sandbox are too heavy for a weekly habit, and the harnesses are what
  Wilco actually wants compared. Kept: the 30 calibrated items as question source, the store,
  the report. Parked: roster runs, sandbox, cross-vendor judge, guard, importers (optional).
- 2026-09-24 Harnesses first: Claude Code and Codex CLI, scripted through their non-interactive
  modes; Cowork as a manual paste column. Why: both CLIs can be driven from PowerShell; more
  harnesses add flakiness before the habit exists.

- 2026-09-22 Toolchain: Python 3.12, `uv` for env and lockfile, `inspect-ai` pinned per run,
  `modernc`-style pure dependencies avoided where possible (sqlite via stdlib). Why: uv gives a
  reproducible lockfile and fast installs; the run records its own pinned versions.
- 2026-09-22 Sandbox: Inspect Docker sandbox, Docker Desktop confirmed on the laptop. Why:
  agentic coding tasks need an end-state check inside a container, and Inspect ships it.
- 2026-09-22 Cadence: weekly plus on-release, cost not the constraint, EUR 300 per-run runaway
  guard. Why: weekly gives 20 samples per task per model per month and catches drift under an
  unchanged snapshot ID (Wilco, amended from monthly the same day).
- 2026-09-22 Name: modelwatch. Why: modelbench collides with MLCommons ModelBench.
- 2026-09-22 Home: own project folder plus a thin skill in znd-skills later. Why: the private
  task set must not travel with a plugin; the results store needs a home.
- 2026-09-22 Runner: Inspect AI. Why: MIT, all providers used here, Docker sandbox, per-run logs;
  promptfoo now OpenAI-owned; HELM in maintenance; OpenAI Evals shutting down 2026-11-30.
- 2026-09-22 Purpose: own task set, public data imported not re-run. Why: re-running public
  benchmarks costs money and adds no opinion; Epoch and AA publish their series.
- 2026-09-22 Repo: private GitHub repository. Why: the task set is the asset; a public repo
  would contaminate it within one training cycle.
