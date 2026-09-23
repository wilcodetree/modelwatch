---
project: modelwatch
date: 2026-09-23
type: hub_agent_update
topic: step 4 voice and Dutch precision anchors complete
---

# modelwatch: Step 4 complete

## Goal

Bring the hub record up to date after modelwatch v0.1 Step 4, without exposing private tasks,
fixtures, completions, or item IDs.

## Done

Step 4 added six voice anchors and four Dutch precision anchors, deterministic pre-checks, a
position-swapped five-point cross-vendor judge, and human calibration. Clean run
`20260923T083904+0200` completed 20 samples with zero HTTP retries and appended 20 judged rows.
Area means in roster order were 0.727 and 0.723 for `voice`, then 0.556 and 0.731 for `dutch`.
Human calibration passed 10/10 against an 8/10 gate. The stores now contain 2,517 rows. All 24
tests and all 22 known completion pairs pass.

## Decisions and why

- Judge Anthropic outputs with fixed release `openrouter/openai/gpt-5.2`, because the direct
  OpenAI account had no credits and OpenRouter preserves the cross-vendor design.
- Keep failed run `20260923T002954+0200` with error notes, because results are append-only.
- Keep all task-level material inside the private repository, because the hub may receive only
  aggregate evidence.

## Open items

Commit, tag `v0.1.0-alpha.4`, and push are Wilco's manual actions. Step 5, coding and
skill-following anchors, is next. Existing roadmap priority and milestone dates do not change.

## Next step

Update the hub one-pager and roadmap to say Steps 1 to 4 are complete and Step 5 is next. Verify
the commit, tag, and push before recording repository publication as complete.

## Files

- `C:\ZND\projects\modelwatch\SESSION_LOG.md`
- `C:\ZND\projects\modelwatch\STATUS.md`
- `C:\ZND\projects\modelwatch\03_logs\calibration.ndjson`
- `C:\ZND\projects\modelwatch\results\results.ndjson`
- `C:\ZND\projects\modelwatch\04_assets\hub_agent_update_2026-09-23_modelwatch_step_4_complete.md`
- Step 4 implementation and private anchors under `C:\ZND\projects\modelwatch\src`, `tests`,
  `config`, and `tasks`.
