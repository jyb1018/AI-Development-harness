#!/usr/bin/env python3
"""Install local instructions without overwriting user changes. Python 3.10+."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
STATE = '.universal-harness/STATE.json'
PROPOSAL = '.universal-harness/AGENTS.proposed.md'


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked_path(target: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError(f'Unsafe relative path: {relative}')
    path = target
    for index, part in enumerate(rel.parts):
        path = path / part
        if path.is_symlink():
            raise ValueError(f'Symlink destination refused: {path}')
        if index < len(rel.parts) - 1 and path.exists() and not path.is_dir():
            raise ValueError(f'Destination parent is not a directory: {path}')
    if path.exists() and not path.is_file():
        raise ValueError(f'Destination is not a regular file: {path}')
    return path


def target_root(value: str) -> Path:
    target = Path(value).expanduser().absolute()
    for part in (target, *target.parents):
        if part.is_symlink():
            raise ValueError(f'Symlink target component refused: {part}')
    target = target.resolve(strict=True)
    if not target.is_dir() or target == Path(target.anchor):
        raise ValueError('Target must be an existing project directory, not a filesystem root')
    if target == ROOT or ROOT in target.parents:
        raise ValueError('Cannot install into the harness source tree')
    return target


def read_state(target: Path) -> dict:
    path = checked_path(target, STATE)
    if not path.exists():
        return {'schema_version': 2, 'files': {}}
    state = json.loads(path.read_text(encoding='utf-8'))
    if (not isinstance(state, dict) or state.get('schema_version') != 2 or not isinstance(state.get('files'), dict)
            or not all(isinstance(k, str) and isinstance(v, str)
                       and re.fullmatch(r'[0-9a-f]{64}', v)
                       for k, v in state['files'].items())):
        raise ValueError('Invalid installer state; inspect it before retrying')
    return state


def require_source_files(relative_paths: list[str]) -> None:
    """Preflight the distribution, never demand skills in the target project."""
    missing = []
    for relative in relative_paths:
        source = ROOT / relative
        for component in (source, *source.parents):
            if component == ROOT:
                break
            if component.is_symlink():
                raise ValueError(f'Symlink source refused: {relative}')
        if not source.is_file():
            missing.append(relative)
    if missing:
        raise ValueError(
            'Incomplete harness source package; no files written.\n'
            + '\n'.join(f'Missing source: {relative}' for relative in missing)
            + '\nUse a complete repository clone or extracted ZIP containing '
              'skills/, profiles/, harness.json and AGENTS.template.md. '
              'Run that copy of scripts/install.py with your empty project as '
              'the target. A .patch or install.py alone is not an installer package.'
        )


def package_files(profile: str) -> tuple[dict, dict[str, bytes]]:
    require_source_files(['harness.json'])
    meta = json.loads((ROOT / 'harness.json').read_text(encoding='utf-8'))
    if (not isinstance(meta, dict) or meta.get('schema_version') != 2
            or not isinstance(meta.get('profiles'), list) or profile not in meta['profiles']):
        raise ValueError('Unsupported package/profile')
    names = meta.get('skills')
    limits = meta.get('limits')
    if (not isinstance(names, list) or not names
            or not all(isinstance(name, str) and re.fullmatch(r'uh-[a-z0-9-]+', name) for name in names)
            or len(names) != len(set(names))
            or not isinstance(limits, dict)
            or type(limits.get('skill_bytes')) is not int or limits['skill_bytes'] <= 0):
        raise ValueError('Invalid package skill inventory or limits')
    # Visible source payload survives copying without hidden directories.
    # The installed layout remains the host's .agents/skills convention.
    sources = {'.universal-harness/profile.md': f'profiles/{profile}.md'}
    for name in meta['skills']:
        if not re.fullmatch(r'uh-[a-z0-9-]+', name):
            raise ValueError('Invalid skill name')
        sources[f'.agents/skills/{name}/SKILL.md'] = f'skills/{name}/SKILL.md'
    support = meta.get('support_files', {})
    if not isinstance(support, dict):
        raise ValueError('Invalid support file mapping')
    reserved = {STATE.casefold(), PROPOSAL.casefold(), '.universal-harness/profile.md'}
    seen = set()
    for destination, source in support.items():
        for value in (destination, source):
            if (not isinstance(value, str) or not value or '\\' in value
                    or Path(value).is_absolute() or any(p in ('', '.', '..') for p in value.split('/'))):
                raise ValueError('Unsafe support file path')
        key = destination.casefold()
        if (not destination.startswith('.universal-harness/') or key in reserved
                or key in seen or source.split('/')[0] not in ('scripts', 'docs', 'integrations')):
            raise ValueError('Unsafe or colliding support file destination')
        seen.add(key)
        sources[destination] = source
    require_source_files(['AGENTS.template.md', *sources.values(),
                          *(['scripts/tooling.py'] if 'uh-tooling' in names else [])])
    payload = {rel: (ROOT / source).read_bytes() for rel, source in sources.items()}
    if 'uh-tooling' in names:
        import tooling
        if any(support.get(dest) != source for dest, source in tooling.SUPPORT_FILES.items()):
            raise ValueError('Incomplete tooling support mapping; no files written')
        tooling.load_catalog(ROOT / 'integrations/tooling.json')
        for name in names:
            raw = payload[f'.agents/skills/{name}/SKILL.md']
            try:
                if len(raw) > limits['skill_bytes'] or tooling.skill_name(raw) != name:
                    raise ValueError('Name mismatch or instruction budget exceeded')
            except (ValueError, UnicodeError) as exc:
                raise ValueError(f'Invalid source skill: {name}; no files written. {exc}') from exc
    return meta, payload


def plan_install(target: Path, profile: str, upgrade: bool,
                 global_skill_roots: list[Path] | None = None) -> tuple[dict[str, bytes], dict]:
    previous = read_state(target)
    meta, wanted = package_files(profile)
    if 'uh-tooling' in meta['skills']:
        # Import after package preflight so install.py alone still gets a useful error.
        import tooling
        scan = tooling.scan_skills(tooling.skill_roots(target, global_skill_roots))
        collisions = [item for item in scan['skills'] if item['name'] in meta['skills']
                      and Path(item['path']).absolute() !=
                      (target / '.agents/skills' / item['name'] / 'SKILL.md').absolute()]
        if collisions:
            raise ValueError('No files written: same-name skills outside the managed destination. '
                             'Choose an active scope after reviewing the host configuration; '
                             'the installer will not remove user files.\n' +
                             '\n'.join(item['name'] + ': ' + item['path'] for item in collisions))
        if scan['warnings']:
            print('SKILL SCAN INCOMPLETE: run tooling doctor --strict; '
                  'unreadable/unsupported definitions were preserved.', file=sys.stderr)
    core = (ROOT / 'AGENTS.template.md').read_bytes()
    agents = checked_path(target, 'AGENTS.md')
    core_managed = not agents.exists() or 'AGENTS.md' in previous['files']
    core_path = 'AGENTS.md' if core_managed else PROPOSAL
    wanted[core_path] = core
    changed = {}
    conflicts = []
    for rel, data in wanted.items():
        path = checked_path(target, rel)
        if not path.exists():
            changed[rel] = data
            continue
        current = path.read_bytes()
        if current == data:
            continue
        if not upgrade:
            conflicts.append(f'{rel}: exists with different content; use --upgrade for managed files')
        elif previous['files'].get(rel) != digest(current):
            conflicts.append(f'{rel}: user-edited or unmanaged; merge manually')
        else:
            changed[rel] = data
    if conflicts:
        raise ValueError('No files written:\n' + '\n'.join(conflicts))
    state = {
        'schema_version': 2,
        'version': meta['version'],
        'profile': profile,
        'core_status': 'managed' if core_managed else 'manual_merge_required',
        'files': {rel: digest(data) for rel, data in sorted(wanted.items())},
    }
    state_bytes = (json.dumps(state, indent=2) + '\n').encode('utf-8')
    state_path = checked_path(target, STATE)
    if not state_path.exists() or state_path.read_bytes() != state_bytes:
        changed[STATE] = state_bytes
    return changed, state


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.uh-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def install(target: Path, profile: str, upgrade: bool = False, dry_run: bool = False,
            global_skill_roots: list[Path] | None = None) -> dict:
    # Plan all conflicts before creating files. State is written last, per-file atomic.
    changed, state = plan_install(target, profile, upgrade, global_skill_roots)
    for rel in changed:
        print(('WOULD WRITE ' if dry_run else 'WRITE ') + rel)
    if not dry_run:
        for rel, data in changed.items():
            atomic_write(checked_path(target, rel), data)
    print(f"{'DRY RUN' if dry_run else 'FILES INSTALLED'} {state['version']} profile={state['profile']}")
    if state['core_status'] == 'manual_merge_required':
        print(f'ACTIVATION PENDING: merge {PROPOSAL} into existing AGENTS.md; it is not auto-loaded.')
    else:
        print('Confirm instruction/skill loading in the host; installed files are not a behavioral certification.')
    old_names = ('thin-process', 'ponytail', 'acceptance-first', 'systematic-debugging',
                 'risk-review', 'external-effects', 'model-drift-audit')
    if any((target / '.agents/skills' / name).exists() for name in old_names):
        print('LEGACY SKILLS PRESENT: preserved; review duplicate activation before use.')
    if 'uh-tooling' in json.loads((ROOT / 'harness.json').read_text(encoding='utf-8'))['skills']:
        print('TOOLING: run python3 .universal-harness/tooling.py doctor . from the target. '
              'No global tool was installed or authenticated.')
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', help='Existing project directory; may be completely empty (no Git or prior harness needed)')
    parser.add_argument('--profile', choices=('generic', 'sol', 'astra'), default='generic')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--upgrade', action='store_true')
    parser.add_argument('--global-skill-root', action='append', type=Path,
                        help='Override global roots for collision preflight; repeat as needed')
    args = parser.parse_args()
    try:
        install(target_root(args.target), args.profile, args.upgrade, args.dry_run, args.global_skill_root)
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'INSTALL FAILED: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
