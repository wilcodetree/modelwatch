---
project: modelwatch
date: 2026-09-24
type: hub_agent_update
topic: v0.1 built in two days, full run incomplete, replanned to v0.2 light
supersedes: hub_agent_update_2026-09-22_modelwatch_approved.md (dates and design)
---

# modelwatch: v0.1 built early and judged too heavy, v0.2 light replaces the run path

**What happened.** Wilco built v0.1 on 2026-09-22 and 2026-09-23 instead of waiting for
2026-10-12: six steps, tags `v0.1.0-alpha.1` to `v0.1.0`, HEAD `9de4689`. Gate 1 passed at its
threshold (8 of 12), judge calibration 10/10, all 30 anchors self-test green. The step 6 full
run (2026-09-23, run `20260923T131454+0200`) is incomplete: 857 usable scores of 1,500 planned,
981 samples recorded, EUR 18.57 spent, provider errors and OpenRouter credit limits blocked the
ten-model comparison, run interrupted, report labelled provisional. Source: the project's
`SESSION_LOG.md` and `STATUS.md`, read 2026-09-24.

**Decision (project level, Wilco 2026-09-24).** The approach is too heavy for a weekly habit.
v0.2 light: 20 standard questions derived from the 30 anchors, run weekly inside Claude Code
and Codex CLI by one PowerShell script (non-interactive modes), answers saved as files, one
judge (Claude Opus via `claude -p`, self-preference bias disclosed), one append-only
`results\weekly.ndjson`, one `reports\weekly.html` curve per area per harness and model, a
Monday 06:00 scheduled task. No API roster, no Docker sandbox, no OpenRouter, plan usage only.
Cowork joins as a manual paste column. The v0.1 Inspect run path is legacy, kept, not deleted.
Spec `C:\ZND\projects\modelwatch\02_roadmap\2026-09-24_v0.2_light_spec.md`, prompts
`2026-09-24_v0.2_session_prompts.md`, decisions `03_logs\decisions.md` 2026-09-24.

**What did NOT happen.** No code changed on 2026-09-24. The 2026-09-23 run was not completed
or re-run. No monthly post was published (a draft exists, `reports\post_draft_2026-09-23.md`,
provisional).

**Hub rows to correct.**
- `DEADLINES.md`: the four modelwatch rows (2026-10-30 gate 1, 2026-11-21 v0.1.0 and gate 2,
  2026-11-30 v0.2.0, 2026-12-19 retro) describe the v0.1 plan. Gate 1 and v0.1.0 are DONE
  2026-09-22/23 (gate 2 provisional, run incomplete). Replace with: 2026-10-12 v0.2 light
  first unattended Monday run judged and charted; 2026-12-07 eight weekly points, v0.3 rolling
  mean and first monthly post; 2026-12-19 retro with BurnMon (unchanged).
- `01_projects\portfolio.md` modelwatch row and `01_projects\modelwatch.md`: replace the
  "Inspect, 30 tasks x 10 models x 5 repeats, EUR 6,000 to 11,000 a year" description with the
  light design; yearly API cost is now near zero (plan usage), a fact worth stating.
- `02_roadmap\roadmap.md` section 1 item 4 sub-entry: v0.1 done early, v0.2 light by 2026-10-12.
- `03_logs\decisions.md`: the 2026-09-22 entry's cost consequence (EUR 6,000 to 11,000 a year)
  is superseded; a short hub-level amendment entry is warranted since the spend changes.
- `00_company\2026-09-22_proposal_modelwatch.md`: add an amendment line at the top pointing to
  the project decision of 2026-09-24; the proposal's opinion stands, its run design does not.
- `znd_os_state.json` modelwatch `next_action`: step 1 of v0.2 light, three sessions, target
  2026-10-12.
