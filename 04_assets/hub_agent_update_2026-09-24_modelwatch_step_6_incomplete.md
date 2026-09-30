---
project: modelwatch
date: 2026-09-24
type: hub_agent_update
topic: step 6 interrupted run and provisional report
---

# modelwatch: Step 6 interrupted, report provisional

## Goal

Bring the hub record up to date after the first full-roster attempt and report generation,
without exposing private task text, fixtures, completions, patches, or item IDs.

## Outcome

Run `20260923T131454+0200` attempted the full dated ten-model roster across all six anchor
areas. The run ended with status `error` after a `KeyboardInterrupt`. Recovery appended 123
unique rows from completed evaluation logs, bringing the run to 981 recorded samples against
1,500 planned. Of those, 857 are usable scores. The other 124 are provider or infrastructure
sample errors; they remain in the append-only store but are excluded from rankings and paired
comparisons.

The run recorded EUR 18.565173. The EUR 300 guard was not reached. Direct and routed provider
failures, including credit-limit responses, prevented a complete comparison. Step 6 and Gate 2
therefore remain incomplete.

The provisional run report, refreshed dashboard, and post draft are available. They state the
coverage limitation prominently and do not present the partial results as a completed benchmark.

## Provisional Gate 2 signal

When restricted to model-area pairs with complete usable coverage, every area contains at least
one pair whose absolute difference is larger than one standard error:

- Hub edits: yes
- Prompt injection: yes
- Voice: yes
- Dutch precision: yes
- Agentic coding: yes
- Skill following: yes

This is directional evidence only. Incomplete model coverage means the hub must not record Gate
2 as passed or failed from this run.

## Verification

- `uv run pytest` passes all 35 tests.
- `uv run modelwatch selftest` passes with 5,923 stored rows.
- `uv run modelwatch selftest --tasks` passes all 30 known completion pairs.
- Rendered checks at desktop and narrow widths found no page-level horizontal overflow or local
  runtime errors. Browser screenshot capture was unavailable, so the visual evidence is limited
  to rendered DOM and layout checks.
- Secret and generated-file formatting scans pass.

## Decisions and why

- Preserve all recovered and failed rows because `results\results.ndjson` is append-only.
- Exclude only provider and infrastructure sample errors from statistics because their zero
  values are not model-performance observations.
- Label every ranking and paired comparison provisional because coverage is incomplete.
- Create no release tag because neither Step 6 nor Gate 2 is complete.

## Hub changes requested

Update the modelwatch one-pager and roadmap to record that the first Step 6 full-roster attempt
was interrupted and that a provisional report exists. Do not mark Step 6, Gate 2, or v0.1.0
complete. Keep the existing roadmap priority and milestone dates unchanged until Wilco chooses
between accepting the incomplete run as historical evidence and authorizing a clean recovery
run.

Keep all task prompts, fixture contents, model completions, patches, and item IDs out of the hub.

## Open items

- Wilco must decide whether to accept this incomplete run as historical evidence or run a clean
  replacement after provider-limit handling is corrected.
- Commit, tag, push, and repository publication remain manual. No `v0.1.0` tag was created.

## Files

- `C:\ZND\projects\modelwatch\reports\20260923T131454+0200.html`
- `C:\ZND\projects\modelwatch\reports\dashboard.html`
- `C:\ZND\projects\modelwatch\reports\post_draft_2026-09-23.md`
- `C:\ZND\projects\modelwatch\runs\20260923T131454+0200\run.json`
- `C:\ZND\projects\modelwatch\results\results.ndjson`
- `C:\ZND\projects\modelwatch\SESSION_LOG.md`
- `C:\ZND\projects\modelwatch\04_assets\hub_agent_update_2026-09-24_modelwatch_step_6_incomplete.md`
