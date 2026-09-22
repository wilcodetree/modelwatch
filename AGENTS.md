# modelwatch

Private, longitudinal benchmark of AI models on ZeroNonsense.dev's own work. Weekly runs
on Inspect AI, public series imported from Epoch AI, Artificial Analysis, LiveBench and METR.
Approved 2026-09-22, build starts 2026-10-12, one session a week.

Proposal (why, design, decisions): `C:\ZND\10_holding\00_company\2026-09-22_proposal_modelwatch.md`
Roadmap (priority order, only here): `C:\ZND\projects\modelwatch\02_roadmap\roadmap.md`
v0.1 spec: `C:\ZND\projects\modelwatch\02_roadmap\2026-09-22_v0.1_spec.md`
Session prompts: `C:\ZND\projects\modelwatch\02_roadmap\2026-09-22_v0.1_session_prompts.md`
Hub one-pager: `C:\ZND\10_holding\01_projects\modelwatch.md`

Root tree instructions: `C:\ZND\AGENTS.md`. Dates: `DEADLINES.md` in this folder.

Rules specific to this project:
- The task set under `tasks\` is private. Task text never appears in a chat, a post, a
  skill or a report. Tasks are only ever run through the harness.
- Model identifiers are exact dated snapshot IDs, never aliases such as `latest`.
- `results\results.ndjson` is append-only. A bad run gets a `notes` value, never a delete.
- Every run records the Inspect version, the task set version and the roster file date.
- No Valona folder, no `C:\dev\Work`, is ever a fixture or a task source.
