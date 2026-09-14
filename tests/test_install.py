import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import install as installer


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.target = self.root / 'project with spaces'
        self.target.mkdir()

    def run_install(self, **options):
        with contextlib.redirect_stdout(io.StringIO()):
            return installer.install(self.target, options.pop('profile', 'generic'), **options)

    def test_fresh_install(self):
        state = self.run_install(profile='astra')
        self.assertEqual(state['core_status'], 'managed')
        self.assertEqual(len(list((self.target / '.agents/skills').glob('*/SKILL.md'))), 7)
        self.assertEqual((self.target / 'AGENTS.md').read_bytes(),
                         (installer.ROOT / 'AGENTS.template.md').read_bytes())
        self.assertFalse((self.target / '.github').exists())
        self.assertFalse((self.target / 'docs').exists())

    def test_dry_run_no_effects(self):
        self.run_install(dry_run=True)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_preserve_existing_agents(self):
        (self.target / 'AGENTS.md').write_text('# User rules\n', encoding='utf-8')
        state = self.run_install()
        self.assertEqual(state['core_status'], 'manual_merge_required')
        self.assertEqual((self.target / 'AGENTS.md').read_text(), '# User rules\n')
        self.assertTrue((self.target / installer.PROPOSAL).exists())
        self.assertNotIn('AGENTS.md', state['files'])

    def test_idempotent(self):
        self.run_install()
        before = {str(p): p.read_bytes() for p in self.target.rglob('*') if p.is_file()}
        self.run_install()
        after = {str(p): p.read_bytes() for p in self.target.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_profile_change_requires_upgrade(self):
        self.run_install(profile='sol')
        with self.assertRaises(ValueError):
            self.run_install(profile='astra')
        state = self.run_install(profile='astra', upgrade=True)
        self.assertEqual(state['profile'], 'astra')

    def test_user_edit_blocks_all_writes(self):
        self.run_install(profile='sol')
        skill = self.target / '.agents/skills/uh-debug/SKILL.md'
        skill.write_text('user edit', encoding='utf-8')
        before = (self.target / '.universal-harness/profile.md').read_bytes()
        with self.assertRaises(ValueError):
            self.run_install(profile='astra', upgrade=True)
        self.assertEqual((self.target / '.universal-harness/profile.md').read_bytes(), before)
        self.assertEqual(skill.read_text(), 'user edit')

    def test_unmanaged_collision(self):
        skill = self.target / '.agents/skills/uh-review/SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_text('existing', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.run_install(upgrade=True)
        self.assertFalse((self.target / 'AGENTS.md').exists())

    def test_directory_collision(self):
        (self.target / 'AGENTS.md').mkdir()
        with self.assertRaises(ValueError):
            self.run_install()

    def test_parent_file_conflict_is_preflighted(self):
        (self.target / '.agents').write_text('not a directory', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.run_install()
        self.assertFalse((self.target / '.universal-harness').exists())

    def test_modified_agents_blocks_upgrade(self):
        self.run_install(profile='sol')
        (self.target / 'AGENTS.md').write_text('custom user rules', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.run_install(profile='astra', upgrade=True)
        self.assertEqual((self.target / 'AGENTS.md').read_text(), 'custom user rules')

    def test_cli_real_install(self):
        result = subprocess.run([sys.executable, str(installer.ROOT / 'scripts/install.py'),
                                 str(self.target), '--profile', 'sol'], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads((self.target / installer.STATE).read_text())['profile'], 'sol')

    def test_invalid_state(self):
        path = self.target / installer.STATE
        path.parent.mkdir()
        path.write_text('{"schema_version":1}', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.run_install()
        self.assertFalse((self.target / 'AGENTS.md').exists())

    def test_symlink_escape(self):
        outside = self.root / 'outside'
        outside.mkdir()
        try:
            (self.target / '.agents').symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Symlink creation unavailable on this host')
        with self.assertRaises(ValueError):
            self.run_install()
        self.assertEqual(list(outside.iterdir()), [])

    def test_relative_traversal(self):
        with self.assertRaises(ValueError):
            installer.checked_path(self.target, '../outside')

    def test_refuse_source_tree_and_root(self):
        for target in (installer.ROOT, Path(installer.ROOT.anchor)):
            with self.assertRaises(ValueError):
                installer.target_root(str(target))

    def test_legacy_skill_preserved(self):
        old = self.target / '.agents/skills/ponytail/SKILL.md'
        old.parent.mkdir(parents=True)
        old.write_text('legacy', encoding='utf-8')
        self.run_install()
        self.assertEqual(old.read_text(), 'legacy')

    def test_managed_older_content_upgrades(self):
        self.run_install()
        file = self.target / '.agents/skills/uh-debug/SKILL.md'
        file.write_text('old package bytes', encoding='utf-8')
        path = self.target / installer.STATE
        state = json.loads(path.read_text())
        state['files']['.agents/skills/uh-debug/SKILL.md'] = installer.digest(file.read_bytes())
        path.write_text(json.dumps(state), encoding='utf-8')
        self.run_install(upgrade=True)
        self.assertEqual(file.read_bytes(), (installer.ROOT / 'skills/uh-debug/SKILL.md').read_bytes())

    def test_cli_invalid_profile(self):
        result = subprocess.run([sys.executable, str(installer.ROOT / 'scripts/install.py'),
                                 str(self.target), '--profile', 'imaginary'], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_temporary_file_cleaned_on_replace_failure(self):
        with patch.object(installer.os, 'replace', side_effect=OSError('simulated')):
            with self.assertRaises(OSError):
                installer.atomic_write(self.target / 'x.md', b'x')
        self.assertEqual(list(self.target.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
