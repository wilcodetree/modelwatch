# modelwatch

Watches AI models on ZeroNonsense.dev's own work, weekly, over years.

Two layers. The public layer imports series that others already collect (Epoch AI, Artificial
Analysis, LiveBench, METR). The private layer runs a 30-task anchor set plus 10 rotating tasks
on Inspect AI against eight to ten models, five repeats each, and stores every sample in an
append-only ndjson plus a SQLite mirror. One HTML report per run, one rolling dashboard, one
monthly opinion post built from four weekly runs.

Start here: `AGENTS.md`, then `02_roadmap\roadmap.md`.
