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
(three runs is a useful pilot, not statistical proof). A faster failure is not an
improvement.

## Record the effective execution setup

Copy `run-record.template.json` for each executed run. Keep `null` for telemetry
that cannot be observed; never infer a value from a model alias or UI label.
At minimum preserve these **separate layers**:

- model identity or alias/snapshot and reasoning effort;
- exact host name **and patch version** (for example Codex `0.155.1`) plus platform;
- request-affecting effective host/model config, including
  `model_reasoning_summary` when applicable;
- harness version/revision/profile and project repository/revision;
- actual permission/sandbox posture and available tools;
- acceptance result, command exits, safety findings, avoidable questions/scope,
  wall time, and usage when the host reports it.

The effective configuration matters because a host patch can change request
defaults without changing the model, harness, or project. When a regression appears
across a host update, hold the other layers fixed when feasible before changing the
harness. Release notes or source diffs can justify a targeted host-compatibility
hypothesis, but they do not substitute for a runnable provider reproduction.

## Host regression cases

The catalog contains three fixed host-boundary cases in addition to product
behavior cases:

- `host-reasoning-summary`: separate host defaults/provider capability from model
  and harness behavior;
- `host-empty-continuation`: respect native loop protection rather than creating
  renamed retries;
- `host-native-verification`: honor native approval/verification denial without
  trying an alternate tool path.

These cases are intentionally host-oriented. They should not become Sol- or
Astra-specific rules unless measured model behavior requires that split.

A reviewer grades required/forbidden behavior from execution evidence. Code and
integration acceptance remain independently executable; model self-grading is
not the sole oracle. Compare safety first, then accepted outcomes and avoidable
questions/scope/ceremony, then time and usage.

Release a changed rule only if observed results justify it without weakening
safety or acceptance. In a small sample, report counts and uncertainty rather
than universal percentages. Keep the old model unavailable case explicit.

## Current status

No complete Sol/Astra controlled comparison is shipped with this repository.
Installer and structure tests validate the package, not model efficacy.
`harness.json` deliberately records both model validations as `not_run`.
Evaluation is opt-in and may incur costs; this repository never auto-runs paid
models on pull requests.
