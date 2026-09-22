# modelwatch, roadmap

Priority order lives here and only here. One session a week from 2026-10-12.

1. v0.1 (2026-11-21): harness on Inspect AI, public-layer importers, 30 anchor tasks in six
   areas with deterministic and cross-vendor-judge scorers, spend guard, flatten to ndjson and
   SQLite, per-run report, full run 1 on 10 models x 5 repeats.
   Spec: `2026-09-22_v0.1_spec.md`. Prompts: `2026-09-22_v0.1_session_prompts.md`.
   Gate 1 after week 44 (2026-10-30), gate 2 after week 47 (2026-11-21).
2. v0.2 (2026-11-30): weekly scheduled run unattended, on-release procedure, drift view
   (same snapshot week over week), rolling dashboard, thin `modelwatch` skill in
   `C:\ZND\projects\znd-skills` that reads the store and drafts the monthly post.
3. v0.3 (2026-12-19): 10 rotating tasks and the quarterly rotation rule, judge calibration
   report, first monthly post published, retro: keep, adapt or park.
4. Later, not planned: Foreman reads `results.sqlite` for model routing; Terminal-Bench 4.0 via
   Harbor as an optional public re-run; Dutch task set as a published gap analysis.

Weeks, one session each: 42 skeleton, 43 public layer, 44 anchor batch 1, 45 anchor batch 2,
46 anchor batch 3, 47 full run 1, 48 schedule and skill, Dec retro. A slipped week slips
every later row; nothing is squeezed into the same week.

Full reasoning, trade-offs and decisions: the proposal,
`C:\ZND\10_holding\00_company\2026-09-22_proposal_modelwatch.md`.
