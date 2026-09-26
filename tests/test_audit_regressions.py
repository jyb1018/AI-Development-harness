"""Boundary regressions from the 3.0 audit; never call a model or provider."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import install as installer
import tooling
import validate


class AuditRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def package(self):
        dest = self.root / 'source'
        shutil.copytree(ROOT, dest, ignore=shutil.ignore_patterns('.git', '__pycache__'))
        return dest

    def symlink(self, link, target):
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest('Symlinks unavailable')

    def test_name_requires_yaml_separator(self):
        with self.assertRaises(ValueError):
            tooling.skill_name(b'---\nname:find-skills\ndescription: Demo\n---\n')

    def test_missing_empty_or_collection_description_is_not_routable(self):
        bad = ['', 'description:', 'description:   ', 'description: ""', 'description: null',
               'description: [unterminated', 'description: {}',
               'description: ok\ndescription: duplicate', 'description: |']
        for description in bad:
            with self.subTest(description=description), self.assertRaises(ValueError):
                tooling.skill_name(f'---\nname: demo\n{description}\n---\n'.encode())

    def test_quoted_and_multiline_descriptions_remain_supported(self):
        for description in ['description: "Useful: workflow"',
                            "description: 'User''s workflow'",
                            'description: >-\n  First line\n  second line',
                            'description: |\n  Exact workflow']:
            with self.subTest(description=description):
                self.assertEqual(tooling.skill_name(
                    f'---\nname: demo\n{description}\n---\n'.encode()), 'demo')

    def test_alias_visits_consume_scan_budget(self):
        skill = self.root / 'original'
        skill.mkdir()
        (skill / 'SKILL.md').write_text('---\nname: demo\ndescription: Demo\n---\n')
        root = self.root / 'skills'
        root.mkdir()
        for index in range(12):
            self.symlink(root / f'alias-{index:02}', skill)
        with patch.object(tooling, 'MAX_DIRS', 4):
            report = tooling.scan_skills([('global', root)])
        self.assertTrue(report['warnings'])
        self.assertLessEqual(len(report['skills']), 3)  # root is a visit too

    def test_dangling_skill_link_is_visible(self):
        self.symlink(self.root / 'broken', self.root / 'missing')
        report = tooling.scan_skills([('global', self.root)])
        self.assertTrue(any('broken' in warning for warning in report['warnings']))

    def test_invalid_state_shapes_fail_cleanly_and_preserve_files(self):
        target = self.root / 'target'
        target.mkdir()
        state = target / installer.STATE
        state.parent.mkdir()
        for value in [[], None, True, 'state']:
            with self.subTest(value=value):
                state.write_text(json.dumps(value))
                before = state.read_bytes()
                result = subprocess.run([sys.executable, str(ROOT / 'scripts/install.py'), str(target)],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 1)
                self.assertIn('Invalid installer state', result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                self.assertEqual(state.read_bytes(), before)
                self.assertFalse((target / 'AGENTS.md').exists())

    def test_invalid_source_skill_fails_before_target_writes(self):
        package = self.package()
        target = self.root / 'target'
        target.mkdir()
        skill = package / 'skills/uh-debug/SKILL.md'
        bad = [b'no frontmatter', b'---\nname: wrong-name\ndescription: Demo\n---\n',
               b'---\nname: uh-debug\n---\n', b'\xff',
               b'---\nname: uh-debug\ndescription: Demo\n---\n' + b'x' * 4000]
        with patch.object(installer, 'ROOT', package):
            for raw in bad:
                with self.subTest(raw=raw[:60]):
                    skill.write_bytes(raw)
                    with self.assertRaises(ValueError), contextlib.redirect_stdout(io.StringIO()):
                        installer.install(target, 'generic', global_skill_roots=[])
                    self.assertEqual(list(target.iterdir()), [])

    def test_invalid_manifest_shapes_fail_before_target_writes(self):
        package = self.package()
        target = self.root / 'target'
        target.mkdir()
        manifest = package / 'harness.json'
        original = json.loads(manifest.read_text())
        cases = [[], None, {**original, 'skills': 'uh-debug'},
                 {**original, 'skills': original['skills'] + ['uh-debug']},
                 {**original, 'profiles': 'generic'}, {**original, 'limits': None}]
        with patch.object(installer, 'ROOT', package):
            for value in cases:
                with self.subTest(value=value):
                    manifest.write_text(json.dumps(value))
                    with self.assertRaises(ValueError), contextlib.redirect_stdout(io.StringIO()):
                        installer.install(target, 'generic', global_skill_roots=[])
                    self.assertEqual(list(target.iterdir()), [])

    def test_tooling_support_cannot_be_omitted_or_corrupted(self):
        package = self.package()
        target = self.root / 'target'
        target.mkdir()
        manifest = package / 'harness.json'
        original = json.loads(manifest.read_text())
        with patch.object(installer, 'ROOT', package):
            for destination in original['support_files']:
                shutil.rmtree(target)
                target.mkdir()
                value = json.loads(json.dumps(original))
                del value['support_files'][destination]
                manifest.write_text(json.dumps(value))
                with self.subTest(missing=destination):
                    with self.assertRaises(ValueError), contextlib.redirect_stdout(io.StringIO()):
                        installer.install(target, 'generic', global_skill_roots=[])
                    self.assertEqual(list(target.iterdir()), [])
            manifest.write_text(json.dumps(original))
            shutil.rmtree(target)
            target.mkdir()
            (package / 'integrations/tooling.json').write_text('{broken')
            with self.assertRaises(ValueError), contextlib.redirect_stdout(io.StringIO()):
                installer.install(target, 'generic', global_skill_roots=[])
            self.assertEqual(list(target.iterdir()), [])

    def test_validator_reports_nonobject_record_and_setup(self):
        package = self.package()
        path = package / 'evals/run-record.template.json'
        original = json.loads(path.read_text())
        for value in [[], None, {**original, 'setup': []}, {**original, 'setup': None}]:
            with self.subTest(value=value):
                path.write_text(json.dumps(value))
                errors = validate.validate(package)
                self.assertTrue(errors)

    def test_summary_keeps_strict_failure_and_route_evidence(self):
        path = self.root / '.agents/skills/broken/SKILL.md'
        path.parent.mkdir(parents=True)
        path.write_text('broken')
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/tooling.py'), 'route',
                                str(self.root), '--no-global-skills', '--strict', '--summary',
                                '--capability', 'repository', '--available', 'github'],
                               capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assertEqual(report['counts']['warnings'], 1)
        self.assertIsNone(report['route']['candidate'])
        self.assertEqual(report['readiness'], 'unverified')
        self.assertNotIn('skills', report)

    def test_summary_output_does_not_expand_with_skill_catalog(self):
        for index in range(100):
            path = self.root / f'.agents/skills/skill-{index}/SKILL.md'
            path.parent.mkdir(parents=True)
            path.write_text(f'---\nname: skill-{index}\ndescription: Demo\n---\n')
        command = [sys.executable, str(ROOT / 'scripts/tooling.py'), 'doctor',
                   str(self.root), '--no-global-skills']
        full = subprocess.run(command, capture_output=True, text=True, timeout=10)
        small = subprocess.run(command + ['--summary'], capture_output=True, text=True, timeout=10)
        self.assertEqual(full.returncode, 0, full.stderr)
        self.assertEqual(small.returncode, 0, small.stderr)
        self.assertEqual(len(json.loads(full.stdout)['skills']), 100)
        self.assertEqual(json.loads(small.stdout)['counts']['skills'], 100)
        self.assertLess(len(small.stdout), len(full.stdout) // 10)


if __name__ == '__main__':
    unittest.main()
