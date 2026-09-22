---
project: modelwatch
date: 2026-09-22
type: hub_agent_update
topic: gate 1 passed after scorer recalibration and anchor hardening
---

# modelwatch: Gate 1 passed

**What happened.** Step 3 of the modelwatch v0.1 specification is complete. The project now
has a five-file synthetic hub fixture, seven private `hub_edits` anchors, five private
`injection` anchors, deterministic scorers, known-good and known-bad calibration, task
self-tests, repeat-level standard errors, and paired model differences per item. No source
material from `C:\ZND\10_holding`, Valona, or client folders entered the fixture or task set.

**Gate 1 result.** The first live batch exposed three measurement defects. These were repaired
without lowering the gate or increasing the three-repeat design. Six items where both models
still behaved identically were then hardened and versioned `2.0.0`. Run
`20260922T230354+0200` evaluated 12 items on the two dated roster models with three repeats,
for 72 samples. Eight of twelve items showed an absolute paired difference larger than one
standard error. Gate 1 therefore passes exactly at its required threshold.

**Evidence.** The run appended 72 rows to both result stores, bringing
`C:\ZND\projects\modelwatch\results\results.ndjson` to 2,477 rows. The task-set version is
`1.0.0`. `uv run modelwatch selftest --tasks` passed all 12 known completion pairs and
`uv run pytest -q` passed 15 tests. The aggregate report is
`C:\ZND\projects\modelwatch\reports\20260922T230354+0200.html`; the implementation record is
in `C:\ZND\projects\modelwatch\SESSION_LOG.md`.

**Hub changes requested.** Mark the 2026-10-30 modelwatch Gate 1 milestone complete, with the
note that it passed 8 of 12 at the threshold after scorer recalibration and anchor hardening.
Keep the existing roadmap priority and later dates unchanged. Step 4, anchor batch 2 for voice
and Dutch precision, remains the next roadmap work.

**Private boundary.** Do not copy task prompts, fixture contents, model completions, or item IDs
into the hub. Hub-facing material may use only the aggregate Gate 1 result, run ID, versions,
test status, and report path recorded above.

**Repository action.** Commit, tag `v0.1.0-alpha.3`, and push remain Wilco's manual actions;
the hub agent must verify them before recording repository publication as complete.
