# Changelog

## 2.0.1 — 2026-09-14

- Fix fresh installation from the published source tree, which lacked the hidden
  `.agents/skills` payload. Restore all seven original v2 skills unchanged under
  visible `skills/`; install them into the target's `.agents/skills/` as before.
- Preflight source completeness and explain clone/ZIP versus patch-only usage
  before writing any target files. Installation does not require prior skills,
  a v1 harness, Git history, or running from a particular working directory.
- Restore the omitted validation workflow and ignore file. Add CLI regression
  coverage for all profiles, visible-only copies, extracted ZIPs, missing payload,
  and existing-install compatibility. No model-policy/profile changes.

## 2.0.0 — 2026-09-14

- First repository release; replaces the earlier 1.0.0 conversation ZIP design.
- One compact consumer policy, shared by Sol and Astra, with optional named profiles.
- Seven namespaced, independently written skills; explicit Karpathy/Ponytail/Superpowers provenance.
- No universal full-Superpowers auto-trigger, mandatory multi-agent chain, or per-commit stop.
- Clarification depends on decision impact; test corrections are allowed with contract evidence.
- Completion distinguishes source, local integration, deployed verification, and release.
- Safe installer: dry-run, update ownership hashes, symlink rejection, collision detection, existing AGENTS preservation.
- Separate package regression tests from unevaluated model-behavior cases.
- Replaces v1's coarse hash/issue watcher design with an explicit semantic review scheduling contract.
- Preserves the repository's existing LICENSE; does not import private project material.

## 1.0.0 — prior conversation package

Not a prior commit of this repository. Original ZIP used seven broad skills,
a larger core, a shell installer, and a document-fingerprint GitHub watcher.
No claim is made that its model behavior or live watcher was validated.
