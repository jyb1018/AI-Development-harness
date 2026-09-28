"""Deterministic installer ownership/migration tests, not model behavior tests."""
import contextlib
import copy
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


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*')
            if p.is_file() and not p.is_symlink()}


class ManagedAgentsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.package = self.root / 'source'
        self.target = self.root / 'project with spaces'
        self.package.mkdir()
        self.target.mkdir()
        # A minimal, explicit fixture exercises the real installer without tooling.
        # Full distribution/tooling is covered separately by the repository suite.
        self.meta = {'schema_version': 2, 'version': '3.0.0',
                     'core': 'AGENTS.template.md', 'bootstrap': 'AGENTS.bootstrap.md',
                     'profiles': ['generic', 'astra'], 'skills': ['uh-example'],
                     'limits': {'skill_bytes': 4000}, 'support_files': {}}
        (self.package / 'harness.json').write_text(json.dumps(self.meta), encoding='utf-8')
        (self.package / 'AGENTS.template.md').write_bytes(b'# Generic harness core\n')
        self.template = (ROOT / 'AGENTS.bootstrap.md').read_bytes().replace(b'\r\n', b'\n')
        (self.package / 'AGENTS.bootstrap.md').write_bytes(self.template)
        (self.package / 'profiles').mkdir()
        for name in self.meta['profiles']:
            (self.package / 'profiles' / (name + '.md')).write_bytes(name.encode())
        skill = self.package / 'skills/uh-example/SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_bytes(b'---\nname: uh-example\ndescription: Test fixture\n---\n')
        self.root_patch = patch.object(installer, 'ROOT', self.package)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.agents = self.target / 'AGENTS.md'

    def run_install(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return installer.install(self.target, kwargs.pop('profile', 'generic'),
                                     global_skill_roots=[], **kwargs)

    def state(self):
        return json.loads((self.target / installer.STATE).read_text(encoding='utf-8'))

    def write_state(self, state):
        path = self.target / installer.STATE
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(state), encoding='utf-8')

    def legacy(self, original=b'# Legacy core\n', edited=None, proposal=False):
        self.agents.write_bytes(original if edited is None else edited)
        state = {'schema_version': 2, 'version': '3.0.0', 'profile': 'generic',
                 'core_status': 'manual_merge_required' if proposal else 'managed',
                 'files': {}}
        if proposal:
            path = self.target / installer.PROPOSAL
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(original)
            state['files'][installer.PROPOSAL] = installer.digest(original)
        else:
            state['files']['AGENTS.md'] = installer.digest(original)
        self.write_state(state)

    def assert_no_writes(self, **kwargs):
        before = snapshot(self.target)
        with self.assertRaises(ValueError):
            self.run_install(**kwargs)
        self.assertEqual(snapshot(self.target), before)

    def test_fresh_install_separates_core_and_block_ownership(self):
        state = self.run_install()
        self.assertEqual(self.agents.read_bytes(), self.template)
        self.assertEqual((self.target / installer.CORE).read_bytes(), b'# Generic harness core\n')
        self.assertEqual(state['schema_version'], 3)
        self.assertEqual(state['core_status'], 'managed_block')
        self.assertNotIn('AGENTS.md', state['files'])
        start, end = installer.managed_span(self.agents.read_bytes())
        self.assertEqual(state['agents']['sha256'], installer.digest(self.agents.read_bytes()[start:end]))

    def test_existing_domain_rules_are_preserved_byte_for_byte(self):
        for original in (b'', b'# Rules', b'# Rules\n', b'# Rules\r\n',
                         b'\xef\xbb\xbf# Rules\r\n',
                         '# 규칙\r\n- 승인 없이 모델을 실행하지 않습니다.\r\n'.encode(),
                         b'---\ntitle: project\n---\n# Rules\n'):
            with self.subTest(original=original):
                # Each input is a genuinely fresh project.
                for child in self.target.iterdir():
                    shutil.rmtree(child) if child.is_dir() else child.unlink()
                self.agents.write_bytes(original)
                self.run_install()
                after = self.agents.read_bytes()
                self.assertTrue(after.startswith(original))
                self.assertEqual(after.count(installer.BEGIN), 1)
                self.assertNotIn('AGENTS.md', self.state()['files'])

    def test_unrelated_and_nested_agents_are_untouched(self):
        nested = self.target / 'src/AGENTS.md'
        nested.parent.mkdir()
        nested.write_bytes(b'# Scoped domain rules\n')
        self.run_install()
        self.assertEqual(nested.read_bytes(), b'# Scoped domain rules\n')

    def test_repeat_install_is_idempotent(self):
        self.run_install()
        before = snapshot(self.target)
        self.run_install()
        self.assertEqual(snapshot(self.target), before)

    def test_project_edits_do_not_block_upgrade_or_become_owned(self):
        self.run_install()
        original_block = self.agents.read_bytes()
        prefix = '# 승인 경계\r\n- GPU 작업은 명시적 승인 후 실행\r\n'.encode()
        suffix = b'\n# ADR routing\nRead policy only when relevant.\n'
        self.agents.write_bytes(prefix + original_block + suffix)
        self.run_install(upgrade=True, profile='astra')
        self.assertEqual(self.agents.read_bytes(), prefix + original_block + suffix)
        self.assertNotIn('AGENTS.md', self.state()['files'])

    def test_bootstrap_upgrade_preserves_both_sides(self):
        self.run_install()
        prefix, suffix = b'\xef\xbb\xbf# Domain\r\n', b'\r\n# After\r\n'
        start, end = installer.managed_span(self.agents.read_bytes())
        original_block = self.agents.read_bytes()[start:end]
        self.agents.write_bytes(prefix + original_block + suffix)
        new_template = self.template.replace(b'## Universal Harness bootstrap', b'## Updated harness bootstrap')
        (self.package / 'AGENTS.bootstrap.md').write_bytes(new_template)
        self.run_install(upgrade=True)
        start, end = installer.managed_span(self.agents.read_bytes())
        self.assertEqual(self.agents.read_bytes()[:start], prefix)
        self.assertEqual(self.agents.read_bytes()[end:], suffix)
        self.assertIn(b'Updated harness', self.agents.read_bytes()[start:end])

    def test_crlf_block_upgrade_preserves_crlf_and_bom(self):
        self.agents.write_bytes(b'\xef\xbb\xbf# Domain\r\n')
        self.run_install()
        before = self.agents.read_bytes()
        start, end = installer.managed_span(before)
        (self.package / 'AGENTS.bootstrap.md').write_bytes(self.template.replace(b'## Universal', b'## Updated Universal'))
        self.run_install(upgrade=True)
        after = self.agents.read_bytes()
        new_start, new_end = installer.managed_span(after)
        self.assertEqual(after[:new_start], before[:start])
        self.assertEqual(after[new_end:], before[end:])
        self.assertNotIn(b'\n', after[new_start:new_end].replace(b'\r\n', b''))

    def test_bootstrap_version_change_requires_upgrade(self):
        self.run_install()
        (self.package / 'AGENTS.bootstrap.md').write_bytes(self.template.replace(b'## Universal', b'## Updated Universal'))
        self.assert_no_writes()

    def test_core_edit_blocks_all_writes(self):
        self.run_install()
        (self.target / installer.CORE).write_bytes(b'# User customized core\n')
        self.assert_no_writes(upgrade=True, profile='astra')

    def test_modified_block_is_not_overwritten(self):
        self.run_install()
        self.agents.write_bytes(self.agents.read_bytes().replace(b'## Universal', b'## Customized Universal'))
        self.assert_no_writes(upgrade=True, profile='astra')

    def test_matching_new_block_does_not_silently_reset_old_hash(self):
        self.run_install()
        new = self.template.replace(b'## Universal', b'## Updated Universal')
        self.agents.write_bytes(new)
        (self.package / 'AGENTS.bootstrap.md').write_bytes(new)
        self.assert_no_writes(upgrade=True)
        self.run_install(upgrade=True, adopt_agents_block=True)

    def test_removed_block_is_not_automatically_reinserted(self):
        self.run_install()
        self.agents.write_bytes(b'# Only domain rules remain\n')
        self.assert_no_writes(upgrade=True)

    def test_deleted_agents_requires_manual_recovery(self):
        self.run_install()
        self.agents.unlink()
        self.assert_no_writes(upgrade=True)

    def test_duplicate_malformed_fenced_and_reversed_markers_fail_closed(self):
        invalid = [self.template + self.template,
                   installer.BEGIN + b'\n# Unclosed\n',
                   installer.END + b'\n' + installer.BEGIN,
                   b'```md\n' + self.template + b'```\n',
                   b'~~~md\n' + self.template + b'~~~\n',
                   self.template.replace(installer.BEGIN, b'  ' + installer.BEGIN),
                   self.template.replace(installer.BEGIN, b'<!-- UNIVERSAL-HARNESS:BEGIN-->'),
                   b'prefix ' + self.template]
        for content in invalid:
            with self.subTest(content=content[:60]):
                self.agents.write_bytes(content)
                self.assert_no_writes(upgrade=True, adopt_agents_block=True)

    def test_closed_code_example_without_reserved_markers_is_preserved(self):
        original = b'```python\nx = 1\n```\n'
        self.agents.write_bytes(original)
        self.run_install()
        self.assertTrue(self.agents.read_bytes().startswith(original))

    def test_unclosed_fence_does_not_get_an_inactive_bootstrap(self):
        self.agents.write_bytes(b'```md\nunfinished example\n')
        self.assert_no_writes()

    def test_preexisting_exact_block_requires_explicit_adoption(self):
        content = self.template + b'\n# Domain rules\n'
        self.agents.write_bytes(content)
        self.assert_no_writes()
        self.run_install(adopt_agents_block=True)
        self.assertEqual(self.agents.read_bytes(), content)

    def test_adoption_cannot_bless_arbitrary_block(self):
        self.agents.write_bytes(self.template.replace(b'## Universal', b'## Custom Universal'))
        self.assert_no_writes(adopt_agents_block=True)

    def test_untouched_legacy_whole_file_migrates_with_upgrade(self):
        self.legacy()
        self.assert_no_writes()
        state = self.run_install(upgrade=True)
        self.assertEqual(self.agents.read_bytes(), self.template)
        self.assertEqual(state['schema_version'], 3)
        self.assertNotIn('AGENTS.md', state['files'])

    def test_edited_legacy_whole_file_needs_manual_split(self):
        self.legacy(edited=b'# Legacy core\n# User domain invariants\n')
        self.assert_no_writes(upgrade=True)
        reconciled = b'# User domain invariants\n\n' + self.template
        self.agents.write_bytes(reconciled)
        self.run_install(upgrade=True, adopt_agents_block=True)
        self.assertEqual(self.agents.read_bytes(), reconciled)

    def test_legacy_proposal_is_preserved_but_retired_from_ownership(self):
        self.legacy(proposal=True, edited=b'# User rules\n# Manually merged old core\n')
        old = (self.target / installer.PROPOSAL).read_bytes()
        self.assert_no_writes(upgrade=True)
        self.agents.write_bytes(b'# User rules\n' + self.template)
        self.run_install(upgrade=True, adopt_agents_block=True)
        self.assertEqual((self.target / installer.PROPOSAL).read_bytes(), old)
        self.assertNotIn(installer.PROPOSAL, self.state()['files'])

    def test_adoption_does_not_bypass_a_core_conflict(self):
        self.run_install()
        (self.target / installer.CORE).write_bytes(b'Custom core')
        self.assert_no_writes(upgrade=True, adopt_agents_block=True)

    def test_dry_run_never_writes_including_state(self):
        self.agents.write_bytes(b'# Project\n')
        before = snapshot(self.target)
        self.run_install(dry_run=True)
        self.assertEqual(snapshot(self.target), before)

    def test_missing_core_or_bootstrap_source_fails_before_writes(self):
        for name in ('AGENTS.template.md', 'AGENTS.bootstrap.md'):
            with self.subTest(name=name):
                path = self.package / name
                original = path.read_bytes()
                path.unlink()
                self.assert_no_writes()
                path.write_bytes(original)

    def test_invalid_bootstrap_source_fails_before_writes(self):
        for bad in (b'not a bootstrap', self.template * 2,
                    b'# project rules outside managed block\n' + self.template,
                    self.template.replace(b'.universal-harness/CORE.md', b'missing.md')):
            with self.subTest(bad=bad[:40]):
                (self.package / 'AGENTS.bootstrap.md').write_bytes(bad)
                self.assert_no_writes()

    def test_future_or_inconsistent_state_is_rejected(self):
        self.run_install()
        valid = self.state()
        variants = []
        for version in (1, 4):
            value = copy.deepcopy(valid)
            value['schema_version'] = version
            variants.append(value)
        for block in (None, [], {}, {'mode': 'managed_block', 'sha256': 'invalid'}):
            value = copy.deepcopy(valid)
            value['agents'] = block
            variants.append(value)
        value = copy.deepcopy(valid)
        value['files']['AGENTS.md'] = installer.digest(self.agents.read_bytes())
        variants.append(value)
        for state in variants:
            with self.subTest(state=state):
                self.write_state(state)
                self.assert_no_writes(upgrade=True)

    def test_core_destination_cannot_be_shadowed_by_support_files(self):
        self.meta['support_files'] = {'.universal-harness/core.MD': 'docs/override.md'}
        (self.package / 'harness.json').write_text(json.dumps(self.meta), encoding='utf-8')
        self.assert_no_writes()

    def test_invalid_utf8_agents_are_preserved(self):
        self.agents.write_bytes(b'\xff\xfe#\0P\0r\0o\0j\0e\0c\0t\0')
        before = snapshot(self.target)
        with self.assertRaises(UnicodeError):
            self.run_install()
        self.assertEqual(snapshot(self.target), before)

    def test_symlink_agents_are_not_followed(self):
        outside = self.root / 'outside.md'
        outside.write_bytes(b'# Outside\n')
        try:
            self.agents.symlink_to(outside)
        except OSError:
            self.skipTest('Symlinks unavailable')
        self.assert_no_writes()
        self.assertEqual(outside.read_bytes(), b'# Outside\n')

    def test_concurrent_project_edit_detected_before_any_install_writes(self):
        self.agents.write_bytes(b'# Original\n')
        real_plan = installer.plan_install
        def concurrent(*args, **kwargs):
            result = real_plan(*args, **kwargs)
            self.agents.write_bytes(b'# Concurrent user edit\n')
            return result
        with patch.object(installer, 'plan_install', side_effect=concurrent):
            with self.assertRaisesRegex(ValueError, 'concurrently'):
                self.run_install()
        self.assertEqual(snapshot(self.target), {'AGENTS.md': b'# Concurrent user edit\n'})

    def test_real_cli_and_dry_run_use_fixture_package(self):
        scripts = self.package / 'scripts'
        scripts.mkdir()
        shutil.copyfile(ROOT / 'scripts/install.py', scripts / 'install.py')
        cmd = [sys.executable, str(scripts / 'install.py'), str(self.target)]
        result = subprocess.run(cmd + ['--dry-run'], capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(snapshot(self.target), {})
        self.agents.write_bytes(self.template + b'\n# Domain\n')
        result = subprocess.run(cmd, capture_output=True, timeout=15)
        self.assertNotEqual(result.returncode, 0)
        result = subprocess.run(cmd + ['--adopt-agents-block'], capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.state()['schema_version'], 3)


if __name__ == '__main__':
    unittest.main()
