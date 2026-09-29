#!/usr/bin/env python3
"""Validate package integrity/format only, never claim model behavior was evaluated."""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def validate_authorization_variants(case: dict) -> list[str]:
    """Check the paired scenario contract, not native approval behavior."""
    expected_counts = {'authorization-revoked': 0, 'status-only-update': 1}
    variants = case.get('variants')
    if not isinstance(variants, list) or not variants:
        return ['Missing or invalid authorization variants']
    errors = []
    seen = set()
    for variant in variants:
        if not isinstance(variant, dict):
            errors.append('Invalid authorization variant: expected object')
            continue
        name = variant.get('id')
        if not isinstance(name, str) or not name.strip():
            errors.append('Invalid authorization variant ID')
            continue
        if name in seen:
            errors.append(f'Duplicate authorization variant ID: {name}')
        seen.add(name)
        prompt = variant.get('prompt')
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append(f'Invalid authorization variant prompt: {name}')
        for field in ('required', 'forbidden'):
            rubric = variant.get(field)
            if (not isinstance(rubric, list) or not rubric
                    or any(not isinstance(item, str) or not item.strip() for item in rubric)):
                errors.append(f'Invalid authorization variant {field}: {name}')
        count = variant.get('expected_effect_count')
        if type(count) is not int or count < 0:
            errors.append(f'Invalid authorization variant effect count: {name}')
        elif name in expected_counts and count != expected_counts[name]:
            errors.append(f'Unexpected authorization variant effect count: {name}')
    missing = sorted(set(expected_counts) - seen)
    if missing:
        errors.append('Missing authorization variants: ' + ', '.join(missing))
    return errors


def validate(root: Path) -> list[str]:
    errors = []
    required = ['README.md', 'LICENSE', 'VERSION', 'AGENTS.md', 'AGENTS.template.md', 'AGENTS.bootstrap.md',
                'harness.json', 'docs/SOURCES.md', 'docs/ADOPTION.md', 'docs/MIGRATION.md',
                'docs/MODELS.md', 'docs/MODEL-UPGRADES.md', 'evals/README.md', 'evals/cases.json',
                'evals/run-record.template.json', 'scripts/install.py', 'scripts/validate.py', '.github/workflows/validate.yml',
                'scripts/tooling.py', 'integrations/tooling.json', 'docs/TOOLING.md',
                'docs/MIGRATION-3.md', 'evals/tooling-cases.json']
    for rel in required:
        if not (root / rel).is_file():
            errors.append(f'Missing: {rel}')
    if errors:
        return errors
    try:
        meta = json.loads((root / 'harness.json').read_text(encoding='utf-8'))
        cases = json.loads((root / 'evals/cases.json').read_text(encoding='utf-8'))
        record = json.loads((root / 'evals/run-record.template.json').read_text(encoding='utf-8'))
        if not all(isinstance(value, dict) for value in (meta, cases, record)):
            raise ValueError('Manifest, cases and run record must be JSON objects')
        if meta['schema_version'] != 2 or cases['schema_version'] != 2:
            errors.append('Unsupported schema')
        if meta['version'] != (root / 'VERSION').read_text(encoding='utf-8').strip():
            errors.append('Version mismatch')
        if meta.get('bootstrap') != 'AGENTS.bootstrap.md' or meta.get('core') != 'AGENTS.template.md':
            errors.append('Invalid core/bootstrap source mapping')
        from install import bootstrap_block
        bootstrap_block((root / 'AGENTS.bootstrap.md').read_bytes())
        core = root / meta['core']
        if core.stat().st_size > meta['limits']['core_bytes']:
            errors.append('Core exceeds instruction budget')
        if len(meta['skills']) != len(set(meta['skills'])):
            errors.append('Duplicate skill name')
        for name in meta['skills']:
            if not re.fullmatch(r'uh-[a-z0-9-]+', name):
                errors.append(f'Invalid skill name: {name}')
                continue
            path = root / 'skills' / name / 'SKILL.md'
            if not path.is_file():
                errors.append(f'Missing skill source: skills/{name}/SKILL.md')
                continue
            text = path.read_text(encoding='utf-8')
            header = re.match(r'\A---\nname: ([a-z0-9-]+)\ndescription: ([^\n]+)\n---\n', text)
            if not header or header[1] != name or len(header[2]) > 1024:
                errors.append(f'Invalid skill frontmatter: {name}')
            if path.stat().st_size > meta['limits']['skill_bytes']:
                errors.append(f'Skill exceeds instruction budget: {name}')
        actual = {p.parent.name for p in (root / 'skills').glob('*/SKILL.md')}
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
            if case['id'] == 'host-authorization-revision':
                errors.extend(validate_authorization_variants(case))
        if cases['kind'] != 'behavioral_scenarios_not_execution_results':
            errors.append('Eval evidence type missing')
        host_case_ids = {
            'host-reasoning-summary', 'host-empty-continuation', 'host-native-verification',
            'host-instruction-lifecycle', 'host-authorization-revision', 'host-compaction-resume'
        }
        missing_host_cases = sorted(host_case_ids - set(ids))
        if missing_host_cases:
            errors.append('Missing host regression eval IDs: ' + ', '.join(missing_host_cases))

        if record.get('schema_version') != 1 or record.get('kind') != 'behavioral_evaluation_run_record':
            errors.append('Invalid eval run-record schema')
        else:
            def require_keys(obj, keys, label):
                if not isinstance(obj, dict):
                    errors.append(f'Invalid eval run-record section: {label}')
                    return
                missing = [key for key in keys if key not in obj]
                if missing:
                    errors.append(f'Missing eval run-record keys in {label}: ' + ', '.join(missing))

            require_keys(record, ['run_id', 'case_id', 'started_at', 'setup', 'results'], 'root')
            setup = record.get('setup', {})
            if not isinstance(setup, dict):
                raise ValueError('Invalid eval run-record section: setup')
            require_keys(setup, ['model', 'model_alias_or_snapshot', 'reasoning_effort', 'host',
                                 'effective_config', 'harness', 'project', 'permissions', 'tools'], 'setup')
            require_keys(setup.get('host', {}), ['name', 'version', 'platform'], 'setup.host')
            require_keys(setup.get('effective_config', {}),
                         ['model_reasoning_summary', 'other_request_affecting_overrides'],
                         'setup.effective_config')
            require_keys(setup.get('harness', {}), ['version', 'revision', 'profile'], 'setup.harness')
            require_keys(setup.get('project', {}), ['repository', 'revision'], 'setup.project')
            require_keys(record.get('results', {}),
                         ['acceptance', 'safety_violations', 'avoidable_questions',
                          'unnecessary_scope_or_ceremony', 'command_exits', 'wall_time_seconds',
                          'usage', 'notes'], 'results')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f'Metadata error: {exc}')
    from tooling import validate_package as validate_tooling_package
    errors.extend(validate_tooling_package(root))
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
