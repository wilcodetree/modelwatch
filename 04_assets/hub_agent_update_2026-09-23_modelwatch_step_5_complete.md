---
project: modelwatch
date: 2026-09-23
type: hub_agent_update
topic: step 5 agentic coding and skill-following anchors complete
---

# modelwatch: Step 5 complete

## Goal

Bring the hub record up to date after modelwatch v0.1 Step 5, without exposing private task
text, fixtures, completions, patches, or item IDs.

## Done

Step 5 added five agentic coding anchors and three skill-following anchors, each backed by
fresh synthetic fixtures and known-good and known-bad patch calibration. The tasks use Inspect
AI 0.3.266 with its documented `react()` agent, Docker sandbox, and bash and Python tools. Area
limits are 60,000 tokens, 900 seconds, and 40 messages. A dated EUR price book now supports a
per-run spend guard and a EUR 2 per-sample ceiling. The deliberately low guard test fired before
paid work began.

Run `20260923T104113+0200` completed all 16 samples across the two dated roster models with zero
HTTP retries. Total calculated cost was EUR 0.310864 and the largest sample cost EUR 0.050924.
All ten live coding samples scored 1.0; the skill-following area produced differentiated model
behavior. The run appended 16 rows, bringing the append-only store to 2,533 rows. All 30 tests
and all 30 known completion pairs pass. Docker cleanup completed, with no Inspect or modelwatch
containers remaining.

## Decisions and why

- Use Inspect AI 0.3.266 `react()` because that pinned release documents it as the available
  default agent and does not expose `basic_agent`.
- Run each agentic sample separately so the EUR guard can evaluate cumulative spend after every
  completed sample.
- Keep all fixtures synthetic and all task-level material inside the private repository so the
  hub receives aggregate evidence only.
- Retain the Windows `socket.AF_UNIX` control-surface warning in the session record. It did not
  affect evaluation, scoring, or Docker cleanup.

## Repository state

Commit `6c41bbcbf2428ca40bed7dff830ab6cd691b3097` is on `main`, local `main` matches
`origin/main`, and remote tag `v0.1.0-alpha.5` resolves to that commit. Repository publication
for Step 5 is complete.

## Open items

Step 6, the full run and report, is next. Existing roadmap priority and milestone dates do not
change. No Step 5 repository publication action remains open.

## Next step

Update the hub one-pager and roadmap to say Steps 1 to 5 are complete and Step 6 is next. Keep
all private task material out of the hub.

## Files

- `C:\ZND\projects\modelwatch\SESSION_LOG.md`
- `C:\ZND\projects\modelwatch\STATUS.md`
- `C:\ZND\projects\modelwatch\results\results.ndjson`
- `C:\ZND\projects\modelwatch\04_assets\hub_agent_update_2026-09-23_modelwatch_step_5_complete.md`
- Step 5 implementation and private anchors under `C:\ZND\projects\modelwatch\src`,
  `C:\ZND\projects\modelwatch\tests`, `C:\ZND\projects\modelwatch\config`, and
  `C:\ZND\projects\modelwatch\tasks`.
