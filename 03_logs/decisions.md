# modelwatch, decisions

Newest on top, each with its why.

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
