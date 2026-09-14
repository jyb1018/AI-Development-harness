"""Exercise delivered files through the real CLI, not preinstalled target fixtures."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.target = self.root / 'empty project'
        self.target.mkdir()

    def visible_copy(self, name='source copy'):
        package = self.root / name
        package.mkdir()
        # Reproduce a copy that omits top-level hidden folders, without
        # giving it .agents from a developer's local working tree.
        for source in ROOT.iterdir():
            if source.name.startswith('.') or source.name == '__pycache__':
                continue
            dest = package / source.name
            if source.is_dir():
                shutil.copytree(source, dest, ignore=shutil.ignore_patterns('__pycache__'))
            else:
                shutil.copy2(source, dest)
        return package

    def cli(self, package, target=None, profile='astra', *options):
        target = target or self.target
        return subprocess.run(
            [sys.executable, str(package / 'scripts/install.py'), str(target),
             '--profile', profile, *options],
            cwd=target, text=True, capture_output=True, timeout=20,
        )

    def assert_installed(self, package, target, profile):
        meta = json.loads((package / 'harness.json').read_text(encoding='utf-8'))
        state = json.loads((target / '.universal-harness/STATE.json').read_text(encoding='utf-8'))
        self.assertEqual(state['profile'], profile)
        self.assertEqual(state['version'], meta['version'])
        self.assertEqual((target / 'AGENTS.md').read_bytes(),
                         (package / 'AGENTS.template.md').read_bytes())
        self.assertEqual((target / '.universal-harness/profile.md').read_bytes(),
                         (package / f'profiles/{profile}.md').read_bytes())
        actual = {p.parent.name for p in (target / '.agents/skills').glob('*/SKILL.md')}
        self.assertEqual(actual, set(meta['skills']))
        for name in meta['skills']:
            self.assertEqual((target / f'.agents/skills/{name}/SKILL.md').read_bytes(),
                             (package / f'skills/{name}/SKILL.md').read_bytes())
        self.assertFalse((target / '.git').exists())
        self.assertFalse((target / 'skills').exists())

    def test_all_profiles_from_visible_only_source_and_target_working_directory(self):
        package = self.visible_copy()
        self.assertFalse((package / '.agents').exists())
        self.assertFalse((package / '.git').exists())
        for profile in ('generic', 'sol', 'astra'):
            with self.subTest(profile=profile):
                target = self.root / profile
                target.mkdir()
                dry_run = self.cli(package, target, profile, '--dry-run')
                self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
                self.assertEqual(list(target.iterdir()), [])
                result = self.cli(package, target, profile)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assert_installed(package, target, profile)
                before = {p.relative_to(target): p.read_bytes()
                          for p in target.rglob('*') if p.is_file()}
                repeated = self.cli(package, target, profile)
                self.assertEqual(repeated.returncode, 0, repeated.stderr)
                self.assertEqual(before, {p.relative_to(target): p.read_bytes()
                                         for p in target.rglob('*') if p.is_file()})

    def test_missing_skill_directory_fails_before_writes(self):
        package = self.visible_copy()
        shutil.rmtree(package / 'skills')
        result = self.cli(package)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Incomplete harness source package', result.stderr)
        self.assertIn('Missing source: skills/uh-karpathy/SKILL.md', result.stderr)
        self.assertIn('complete repository clone or extracted ZIP', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_partial_source_is_preflighted(self):
        for index, missing in enumerate(('skills/uh-review/SKILL.md',
                                         'profiles/astra.md', 'AGENTS.template.md',
                                         'harness.json')):
            with self.subTest(missing=missing):
                package = self.visible_copy(f'partial-{index}')
                (package / missing).unlink()
                result = self.cli(package)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f'Missing source: {missing}', result.stderr)
                self.assertEqual(list(self.target.iterdir()), [])

    def test_script_only_explains_complete_package_requirement(self):
        package = self.root / 'script only'
        (package / 'scripts').mkdir(parents=True)
        shutil.copy2(ROOT / 'scripts/install.py', package / 'scripts/install.py')
        result = self.cli(package)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('install.py alone is not an installer package', result.stderr)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_source_skill_parent_symlink_is_refused(self):
        package = self.visible_copy()
        directory = package / 'skills/uh-debug'
        saved = package / 'debug-saved'
        directory.rename(saved)
        try:
            directory.symlink_to(saved, target_is_directory=True)
        except OSError:
            self.skipTest('Symlink creation unavailable on this host')
        result = self.cli(package)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Symlink source refused: ', result.stderr)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_extracted_zip_installs_without_git_or_prior_harness(self):
        package = self.visible_copy()
        archive = self.root / 'harness.zip'
        with zipfile.ZipFile(archive, 'w') as bundle:
            for path in package.rglob('*'):
                if path.is_file():
                    bundle.write(path, Path('harness') / path.relative_to(package))
        extracted = self.root / 'extracted'
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(extracted)
        source = extracted / 'harness'
        result = self.cli(source)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_installed(source, self.target, 'astra')


if __name__ == '__main__':
    unittest.main()
