# Developing Universal Harness

This repository distributes instructions, not an autonomous agent runtime.
Keep the consumer contract in `AGENTS.template.md`; do not copy it into this file.
Read only the skill/profile/document relevant to the requested change.
Preserve LICENSE and unrelated user work. Do not install into other repositories
or change global Codex settings without a request.

Validate changes with:
```sh
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```
A packaging test is not a Sol/Astra behavioral evaluation. Record that distinction.
Use `evals/README.md` when behavior is actually evaluated; never invent model runs.
Do not make every product task run this repository's harness evaluation suite.
No release, merge, global plugin change, paid API run, or deployment is implied by a PR request.
