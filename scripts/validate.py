#!/usr/bin/env python3
"""Validate package integrity/format only, never claim model behavior was evaluated."""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def validate(root: Path) -> list[str]:
    errors = []
    required = ['README.md', 'LICENSE', 'VERSION', 'AGENTS.md', 'AGENTS.template.md',
                'harness.json', 'docs/SOURCES.md', 'docs/ADOPTION.md', 'docs/MIGRATION.md',
                'docs/MODELS.md', 'docs/MODEL-UPGRADES.md', 'evals/README.md', 'evals/cases.json',
                'scripts/install.py', 'scripts/validate.py', '.github/workflows/validate.yml']
    for rel in required:
        if not (root / rel).is_file():
            errors.append(f'Missing: {rel}')
    if errors:
        return errors
    try:
        meta = json.loads((root / 'harness.json').read_text(encoding='utf-8'))
        cases = json.loads((root / 'evals/cases.json').read_text(encoding='utf-8'))
        if meta['schema_version'] != 2 or cases['schema_version'] != 2:
            errors.append('Unsupported schema')
        if meta['version'] != (root / 'VERSION').read_text(encoding='utf-8').strip():
            errors.append('Version mismatch')
        core = root / meta['core']
        if core.stat().st_size > meta['limits']['core_bytes']:
            errors.append('Core exceeds instruction budget')
        if len(meta['skills']) != len(set(meta['skills'])):
            errors.append('Duplicate skill name')
        for name in meta['skills']:
            if not re.fullmatch(r'uh-[a-z0-9-]+', name):
                errors.append(f'Invalid skill name: {name}')
                continue
            path = root / '.agents/skills' / name / 'SKILL.md'
            text = path.read_text(encoding='utf-8')
            header = re.match(r'\A---\nname: ([a-z0-9-]+)\ndescription: ([^\n]+)\n---\n', text)
            if not header or header[1] != name or len(header[2]) > 1024:
                errors.append(f'Invalid skill frontmatter: {name}')
            if path.stat().st_size > meta['limits']['skill_bytes']:
                errors.append(f'Skill exceeds instruction budget: {name}')
        actual = {p.parent.name for p in (root / '.agents/skills').glob('*/SKILL.md')}
        if actual != set(meta['skills']):
            errors.append('Skill inventory mismatch')
        for profile in meta['profiles']:
            if profile not in ('sol', 'astra', 'generic') or not (root / 'profiles' / f'{profile}.md').is_file():
                errors.append(f'Invalid/missing profile: {profile}')
        ids = [case['id'] for case in cases['cases']]
        if not ids or len(ids) != len(set(ids)):
            errors.append('Empty or duplicated eval IDs')
        for case in cases['cases']:
            if not case['prompt'].strip() or not case['required'] or not case['forbidden']:
                errors.append(f'Invalid eval: {case["id"]}')
        if cases['kind'] != 'behavioral_scenarios_not_execution_results':
            errors.append('Eval evidence type missing')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f'Metadata error: {exc}')
    # Check committed Markdown relative file links, not external availability/anchors.
    for path in root.rglob('*.md'):
        if '.git' in path.parts:
            continue
        text = path.read_text(encoding='utf-8')
        for link in re.findall(r'\]\(([^)\s]+)\)', text):
            if re.match(r'^[a-z]+:', link) or link.startswith('#'):
                continue
            linked = link.split('#', 1)[0]
            if linked and not (path.parent / linked).exists():
                errors.append(f'Broken file link: {path.relative_to(root)} -> {link}')
    return errors


def main() -> int:
    errors = validate(ROOT)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print('Package validation PASS. Model behavioral evaluation: NOT RUN by this command.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
