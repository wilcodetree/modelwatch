# modelwatch, roadmap

Priority order lives here and only here. Replanned 2026-09-24: v0.1 was built 22 to 23 Sep
(tag `v0.1.0`, full run incomplete) and judged too heavy as a weekly habit. v0.2 light is the
path forward; the v0.1 Inspect run path is legacy, kept, not deleted.

1. v0.2 light (target 2026-10-12, three sessions): 20 standard questions from the v0.1 anchors,
   run weekly inside Claude Code and Codex CLI by one PowerShell script, answers saved as files,
   one judge (Claude Opus via `claude -p`, disclosed), `results\weekly.ndjson`, `reports\weekly.html`
   with one line per harness and model per area over weeks, Monday 06:00 scheduled task.
   Spec: `2026-09-24_v0.2_light_spec.md`. Prompts: `2026-09-24_v0.2_session_prompts.md`.
   Gate: first unattended Monday run judged and charted, then it is a habit, not a project.
2. v0.3 (after eight weekly points, about 2026-12-07): four-week rolling mean, quarterly hand
   calibration of the judge (10 answers), Cowork paste column in regular use, first monthly
   opinion post from the curve. Retro 2026-12-19 with BurnMon: keep, adapt or park.
3. Later, not planned: `import --all` as a monthly public-picture refresh beside the curve;
   Copilot CLI and Gemini CLI columns; the thin `modelwatch` skill that drafts the post.

Done: v0.1 (2026-09-22 to 2026-09-23, tags `v0.1.0-alpha.1` to `v0.1.0`): Inspect harness,
importers, 30 calibrated anchors, cross-vendor judge, guard, one incomplete ten-model run
(857 of 1,500 usable scores). Its questions, store and report carry into v0.2.

Full reasoning: `C:\ZND\10_holding\00_company\2026-09-22_proposal_modelwatch.md`, amended by
`03_logs\decisions.md` 2026-09-24.
