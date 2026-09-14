---
name: uh-model-upgrade
description: Assess changed model, host, tool, skill-loading, or prompting behavior using controlled comparisons before changing the harness.
---

# Model and harness change audit

Run on a relevant upgrade or measured regression, not on routine product edits.

Identify the actual model/effort, host version, permissions, tools, installed
plugins/hooks, core revision, and project task. Inspect relevant instruction
sources for duplicate or conflicting rules; report layers you cannot inspect.
Do not assume all versions of a model alias or host behave identically.

Compare the prior and candidate setup using fixed tasks, repository revisions,
test data, budgets, and fresh contexts. Change model and harness separately when
feasible. Keep an existing-harness/new-model arm and a new-harness/new-model arm;
include old-model baselines only if still available. Use `evals/README.md` for
the actual evaluation protocol, not an imagined simulation.

Measure accepted outcomes, safety violations, unnecessary stops/changes, time,
and available usage. Label absent measurements unknown. Check instruction
sensitivity, unwanted ceremony, hidden no-ops, excessive questions, and premature
completion. Do not infer causation from an upgrade happening before a failure.

Recommend no change, one narrowly justified change, or rollback. Re-test the
affected behavior plus related regressions. Release notes trigger evaluation,
not automatic edits, paid runs, model switching, or increased permissions.
