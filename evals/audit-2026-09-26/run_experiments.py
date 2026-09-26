#!/usr/bin/env python3
"""Disposable filesystem/CLI experiments. Not a model behavior benchmark."""
import argparse
import contextlib
import hashlib
import io
import json
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import install as installer
import tooling


def snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and not p.is_symlink() and '.git' not in p.parts}


def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def run(output):
    results = []
    def record(name, setup, function):
        start = time.perf_counter()
        try:
            data = function()
            status = 'PASS'
        except Exception as exc:
            data = {'error': type(exc).__name__, 'message': str(exc)}
            status = 'FAIL'
        results.append({'id': name, 'kind': 'EXECUTED_DETERMINISTIC', 'status': status,
                        'setup': setup, 'observed': data,
                        'seconds': round(time.perf_counter() - start, 6)})

    skeletons = {
        'A-empty': {}, 'B-readme': {'README.md': '# Empty product\n'},
        'C-git-only': {}, 'D-package-json': {'package.json': '{"name":"fixture","private":true}'},
        'E-python': {'pyproject.toml': '[project]\nname="fixture"\nversion="0.0.0"\n', 'src/app.py': ''},
        'F-partial-conflict': {'.agents/skills/uh-debug/SKILL.md': 'unmanaged partial file'},
        'node-backend': {'package.json': '{"scripts":{"test":"node --test"}}', 'src/server.js': '// fixture'},
        'react-frontend': {'package.json': '{"dependencies":{"react":"fixture"}}', 'src/App.tsx': '// fixture'},
        'typescript-monorepo': {'package.json': '{"workspaces":["packages/*"]}', 'packages/api/tsconfig.json': '{}'},
        'python-backend': {'pyproject.toml': '[project]\nname="api"', 'app/main.py': '# fixture'},
        'python-ml': {'requirements.txt': 'torch\n', 'models/model.bin': 'opaque fixture', 'data/split.json': '{}'},
        'cv-ocr': {'requirements.txt': 'opencv-python\n', 'fixtures/labels.json': '{}', 'weights/model.pt': 'opaque fixture'},
        'mixed-language': {'package.json': '{}', 'backend/main.py': '# fixture', 'native/lib.rs': '// fixture'},
        'legacy': {'Makefile': 'test:\n\t@true\n', 'legacy.py': '# fixture'},
        'large-test-suite': {f'tests/test_{i:04}.py': '# fixture' for i in range(300)},
        'poor-documentation': {'src/main.py': '# undocumented fixture'},
    }
    with tempfile.TemporaryDirectory(prefix='uh-audit-') as directory:
        base = Path(directory)
        for case, files in skeletons.items():
            profiles = ('generic', 'sol', 'astra') if case[:2] in ('A-', 'B-', 'C-', 'D-', 'E-', 'F-') else ('generic',)
            for profile in profiles:
                def experiment(case=case, profile=profile, files=files):
                    target = base / (case + '-' + profile)
                    target.mkdir()
                    for name, text in files.items(): write(target, name, text)
                    if case == 'C-git-only':
                        subprocess.run(['git', 'init', '-q', str(target)], check=True, capture_output=True)
                    if case[:2] not in ('A-', 'B-', 'C-', 'D-', 'E-', 'F-'):
                        write(target, 'AGENTS.md', '# Preserve project-specific invariants\n')
                    before = snapshot(target)
                    options = dict(global_skill_roots=[])
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        if case == 'F-partial-conflict':
                            try: installer.install(target, profile, **options)
                            except ValueError: pass
                            else: raise AssertionError('Unmanaged conflict was accepted')
                            assert snapshot(target) == before
                            return {'conflict_rejected': True, 'original_files_preserved': True, 'writes': 0}
                        installer.install(target, profile, dry_run=True, **options)
                        assert snapshot(target) == before
                        state = installer.install(target, profile, **options)
                        after = snapshot(target)
                        installer.install(target, profile, **options)
                        assert snapshot(target) == after
                    assert all(after.get(name) == value for name, value in before.items())
                    command = [sys.executable, str(target / '.universal-harness/tooling.py'),
                               'doctor', str(target), '--no-global-skills', '--strict']
                    process = subprocess.run(command, capture_output=True, text=True, timeout=10)
                    assert process.returncode == 0, process.stderr
                    report = json.loads(process.stdout)
                    assert len(report['skills']) == 8
                    return {'dry_run_no_writes': True, 'idempotent': True, 'original_files_preserved': True,
                            'installed_skills': len(report['skills']), 'doctor_exit': process.returncode,
                            'core_status': state['core_status'], 'new_files': len(after) - len(before)}
                record('bootstrap-' + case + '-' + profile,
                       {'fixture': case, 'profile': profile, 'global_roots': [],
                        'scope': 'installation and discovery only; no app/model run'}, experiment)

        for count in (10, 100, 1000, 2100):
            def scale(count=count):
                root = base / f'scale-{count}'
                for i in range(count):
                    write(root, f'skill-{i:04}/SKILL.md',
                          f'---\nname: skill-{i:04}\ndescription: Scoped synthetic workflow {i}.\n---\nInstruction.\n')
                start = time.perf_counter()
                report = tooling.scan_skills([('global', root)])
                elapsed = time.perf_counter() - start
                expected = min(count, tooling.MAX_DIRS - 1)
                assert len(report['skills']) == expected
                assert bool(report['warnings']) == (count >= tooling.MAX_DIRS)
                return {'definitions_found': len(report['skills']), 'warnings': len(report['warnings']),
                        'scan_seconds': round(elapsed, 6),
                        'json_bytes': len(json.dumps(report).encode())}
            record(f'scale-{count}', {'skills': count, 'one_SKILL_per_directory': True}, scale)

        catalog = tooling.load_catalog(ROOT / 'integrations/tooling.json')
        for mode in ('absent', 'observed', 'offline', 'unrelated-broken-skill'):
            def routing(mode=mode):
                target = base / ('routing-' + mode);target.mkdir()
                if mode == 'unrelated-broken-skill': write(target, '.agents/skills/broken/SKILL.md', 'broken')
                available = () if mode == 'absent' else tuple(catalog['providers'])
                with patch.object(tooling.shutil, 'which', return_value=None):
                    report = tooling.inventory(target, catalog, [], available)
                routes = {name: tooling.route(name, catalog, report, mode == 'offline')
                          for name in catalog['capabilities']}
                if mode in ('absent', 'unrelated-broken-skill'):
                    assert all(route['candidate'] is None for route in routes.values())
                else:
                    assert any(route['candidate'] for route in routes.values())
                assert all(route['readiness'] == 'unverified' for route in routes.values())
                return {name: route['candidate'] for name, route in routes.items()}
            record('route-' + mode, {'host_availability': 'synthetic input, no provider started'}, routing)

        def interrupted():
            target = base / 'interrupted';target.mkdir()
            original = installer.atomic_write
            writes = 0
            def failure(path, data):
                nonlocal writes
                writes += 1
                if writes == 4: raise OSError('injected disk failure')
                original(path, data)
            with contextlib.redirect_stdout(io.StringIO()):
                with patch.object(installer, 'atomic_write', side_effect=failure):
                    try: installer.install(target, 'generic', global_skill_roots=[])
                    except OSError: pass
                    else: raise AssertionError('Failure not injected')
                assert not (target / installer.STATE).exists()
                installer.install(target, 'generic', global_skill_roots=[])
            assert (target / installer.STATE).exists()
            return {'failure_after_writes': 3, 'state_absent_until_retry': True, 'retry_completed': True}
        record('interrupted-install', {'fault': 'SIMULATED I/O error; real installer executed'}, interrupted)
    report = {'base_revision': '218e2a40de5001fbf185c94e2c229148079ebcb9',
              'environment': {'python': sys.version, 'platform': platform.platform()},
              'model_runs': 0, 'results': results}
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    counts = {status: sum(r['status'] == status for r in results) for status in ('PASS', 'FAIL')}
    print(json.dumps(counts))
    return int(counts['FAIL'] > 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    raise SystemExit(run(parser.parse_args().output))
