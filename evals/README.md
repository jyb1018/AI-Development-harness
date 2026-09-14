# Behavioral evaluation — not a CI simulation

`cases.json` is a scenario catalog, not a benchmark result. CI validates its shape
only. Do not grade behavior by searching for phrases in the agent's answer.

## Run a real comparison

Choose representative project tasks (at least a routine bug, an integration,
and a high-risk case) and fixed disposable workspaces. Supply the same code,
inputs, permissions, tools, acceptance checks, and budget to each setup.
Cases are prompts plus rubrics; create a realistic task workspace for each chosen
case rather than asking the model to describe what it would do.

Compare existing model/existing harness, candidate model/existing harness, and
candidate model/v2 where available. Repeat each chosen setup in fresh contexts
(three runs is a useful pilot, not statistical proof). Keep actual model/effort,
host version, repo and harness revision, task, tool log, diff, command exits,
wall time, usage if reported, and acceptance results. Use null/unknown for missing
telemetry. Never manufacture a model identity, review, timestamp, or successful run.

A reviewer grades required/forbidden behavior from execution evidence. Code and
integration acceptance remain independently executable; model self-grading is
not the sole oracle. Compare safety first, then accepted outcomes and avoidable
questions/scope/ceremony, then time and usage. A faster failure is not an improvement.

Release a changed rule only if observed results justify it without weakening
safety or acceptance. In a small sample, report counts and uncertainty rather
than universal percentages. Keep the old model unavailable case explicit.

## Current status

No Sol/Astra behavioral runs are shipped in 2.0.0. Installer and structure tests
validate the package, not model efficacy. `harness.json` deliberately records
both model validations as `not_run`. Evaluation is opt-in and may incur costs;
this repository never auto-runs paid models on pull requests.
