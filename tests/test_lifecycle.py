"""Real local Git/submodule/installer tests; no network, providers, or model runs."""
from __future__ import annotations

import base64
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('uh_lifecycle', ROOT / 'scripts/harness.py')
uh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(uh)


def command(root, *args):
    env = os.environ.copy()
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_AUTHOR_NAME='Test', GIT_AUTHOR_EMAIL='test@example.invalid',
               GIT_COMMITTER_NAME='Test', GIT_COMMITTER_EMAIL='test@example.invalid')
    result = subprocess.run(['git', *args], cwd=root, env=env, capture_output=True, timeout=30)
    if result.returncode:
        raise AssertionError(result.stderr.decode(errors='replace'))
    return result.stdout.decode().strip()


def files(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*')
            if p.is_file() and '.git' not in p.parts
            and not p.is_relative_to(root / uh.MODULE)}


@unittest.skipUnless(shutil.which('git'), 'Git is required for local lifecycle tests')
class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / 'upstream source with spaces'
        self.project = self.root / 'consumer project with spaces'
        self.source.mkdir()
        self.project.mkdir()
        # Isolate every Git command, including the runtime, from real user config.
        self.env = patch.dict(os.environ, {'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull})
        self.env.start()
        self.addCleanup(self.env.stop)
        command(self.source, 'init', '-b', 'main')
        command(self.project, 'init', '-b', 'main')
        self.make_package()
        self.old = self.commit_source('fixture: initial')
        (self.project / 'product.txt').write_bytes(b'not a harness file\n')
        (self.project / 'AGENTS.md').write_bytes('# 도메인 지침\r\n- 모델 실행은 승인 후에만 합니다.\r\n'.encode())
        command(self.project, 'add', '.')
        command(self.project, 'commit', '-m', 'fixture: consumer')
        # Explicit test-only local transport permission, never a runtime default.
        command(self.project, '-c', 'protocol.file.allow=always', 'submodule', 'add',
                str(self.source), uh.MODULE)
        self.module = self.project / uh.MODULE
        self.life = uh.Lifecycle(self.project)

    def make_package(self):
        meta = {'schema_version': 2, 'version': '3.0.0', 'core': 'AGENTS.template.md',
                'bootstrap': 'AGENTS.bootstrap.md', 'profiles': ['generic', 'sol', 'astra'],
                'skills': ['uh-debug'], 'limits': {'skill_bytes': 4000, 'core_bytes': 6500}}
        (self.source / 'harness.json').write_bytes(uh.encode(meta))
        (self.source / 'AGENTS.template.md').write_bytes(b'# Core v1\n')
        (self.source / 'AGENTS.bootstrap.md').write_bytes(
            b'<!-- UNIVERSAL-HARNESS:BEGIN -->\nRead .universal-harness/CORE.md\n'
            b'Read .universal-harness/profile.md\n<!-- UNIVERSAL-HARNESS:END -->\n')
        for profile in meta['profiles']:
            path = self.source / 'profiles' / (profile + '.md')
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(('# ' + profile + '\n').encode())
        path = self.source / 'skills/uh-debug/SKILL.md'
        path.parent.mkdir(parents=True)
        path.write_bytes(b'---\nname: uh-debug\ndescription: Fixture\n---\n')
        for name in ('harness.py', 'harness', 'harness.cmd', 'install.py'):
            path = self.source / 'scripts' / name
            path.parent.mkdir(exist_ok=True)
            shutil.copyfile(ROOT / 'scripts' / name, path)

    def commit_source(self, message):
        command(self.source, 'add', '.')
        command(self.source, 'commit', '-m', message)
        return command(self.source, 'rev-parse', 'HEAD')

    def update(self, version='3.1.0'):
        (self.source / 'AGENTS.template.md').write_bytes(('# Core ' + version + '\n').encode())
        meta = json.loads((self.source / 'harness.json').read_bytes())
        meta['version'] = version
        (self.source / 'harness.json').write_bytes(uh.encode(meta))
        return self.commit_source('fixture: update ' + version)

    def install(self, **kwargs):
        return self.life.install_or_upgrade(initial=True, profile='astra',
                                            global_roots=[], **kwargs)

    def upgrade(self, **kwargs):
        return self.life.install_or_upgrade(global_roots=[], **kwargs)

    def wrapper(self, *args):
        if os.name == 'nt':
            argv = ['cmd', '/c', str(self.project / uh.HOME / 'harness.cmd'), *args]
        else:
            argv = [str(self.project / uh.HOME / 'harness'), *args]
        return subprocess.run(argv, cwd=self.root, capture_output=True, timeout=30)

    def test_first_install_separates_config_lock_state_and_preserves_domain(self):
        original = (self.project / 'AGENTS.md').read_bytes()
        result = self.install(channel='edge')
        self.assertTrue(result['applied'])
        self.assertTrue((self.project / 'AGENTS.md').read_bytes().startswith(original))
        self.assertEqual(self.life.lock()['applied_revision'], self.old)
        self.assertEqual(self.life.config()['profile'], 'astra')
        self.assertEqual(json.loads((self.project / uh.STATE).read_bytes())['schema_version'], 3)
        self.assertEqual(self.life.integrity(), [])
        self.assertNotIn('AGENTS.md', self.life.lock()['files'])

    def test_wrapper_runs_from_an_unrelated_directory(self):
        self.install(channel='edge')
        result = self.wrapper('status')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['applied_revision'], self.old)
        if os.name != 'nt':
            self.assertTrue((self.project / uh.HOME / 'harness').stat().st_mode & stat.S_IXUSR)

    def test_initial_dry_run_is_project_read_only(self):
        before = files(self.project)
        result = self.install(channel='edge', dry_run=True)
        self.assertFalse(result['applied'])
        self.assertEqual(files(self.project), before)
        self.assertEqual(command(self.module, 'rev-parse', 'HEAD'), self.old)

    def test_repeated_install_is_idempotent(self):
        self.install(channel='edge')
        before = files(self.project)
        self.life.install_or_upgrade(initial=True, global_roots=[])
        self.assertEqual(files(self.project), before)

    def test_status_is_offline_and_does_not_claim_remote_update(self):
        self.install(channel='edge')
        original = uh.git
        def checked(root, *args):
            self.assertFalse(set(args) & {'fetch', 'ls-remote'})
            return original(root, *args)
        before = files(self.project)
        with patch.object(uh, 'git', side_effect=checked):
            result = self.life.status()
        self.assertFalse(result['network'])
        self.assertIn('not_checked', result['remote_update'])
        self.assertEqual(files(self.project), before)

    def test_check_discovers_update_without_changing_source_or_files(self):
        self.install(channel='edge')
        new = self.update()
        before = files(self.project)
        result = self.life.select(self.life.config())
        self.assertEqual(result['revision'], new)
        self.assertEqual(command(self.module, 'rev-parse', 'HEAD'), self.old)
        self.assertEqual(files(self.project), before)

    def test_pull_changes_only_source_not_installed_runtime_or_index(self):
        self.install(channel='edge')
        new = self.update()
        before = files(self.project)
        index = command(self.project, 'ls-files', '--stage')
        result = self.life.pull()
        self.assertEqual(result['source_revision'], new)
        self.assertFalse(result['applied'])
        self.assertEqual(files(self.project), before)
        self.assertEqual(command(self.project, 'ls-files', '--stage'), index)
        self.assertTrue(self.life.status()['source_not_applied'])
        self.assertIn('AGENTS.template.md', self.life.diff())

    def test_online_upgrade_fetches_and_applies_together(self):
        self.install(channel='edge')
        new = self.update()
        result = self.upgrade()
        self.assertEqual(result['applied_revision'], new)
        self.assertEqual(command(self.module, 'rev-parse', 'HEAD'), new)
        self.assertEqual(self.life.lock()['applied_revision'], new)
        self.assertEqual((self.project / uh.HOME / 'CORE.md').read_bytes(), b'# Core 3.1.0\n')
        self.assertFalse((self.project / uh.JOURNAL).exists())
        self.assertEqual(self.life.integrity(), [])

    def test_offline_upgrade_applies_pulled_source_without_fetch(self):
        self.install(channel='edge')
        new = self.update()
        self.life.pull()
        with patch.object(self.life, 'fetch_candidate', side_effect=AssertionError('fetch')):
            result = self.upgrade(offline=True)
        self.assertEqual(result['applied_revision'], new)

    def test_upgrade_dry_run_never_fetches_or_updates_files(self):
        self.install(channel='edge')
        self.update()
        before = files(self.project)
        with patch.object(self.life, 'fetch_candidate', side_effect=AssertionError('fetch')):
            result = self.upgrade(dry_run=True)
        self.assertEqual(result['selection']['channel'], 'current_checkout')
        self.assertEqual(files(self.project), before)
        self.assertEqual(command(self.module, 'rev-parse', 'HEAD'), self.old)

    def test_project_and_unrelated_work_survive_update(self):
        self.install(channel='edge')
        agents = (self.project / 'AGENTS.md').read_bytes() + '\n- 평가 데이터는 바꾸지 않습니다.\n'.encode()
        (self.project / 'AGENTS.md').write_bytes(agents)
        (self.project / 'product.txt').write_bytes(b'uncommitted product work')
        command(self.project, 'add', 'product.txt')
        index = command(self.project, 'ls-files', '--stage')
        self.update()
        self.upgrade()
        self.assertEqual((self.project / 'AGENTS.md').read_bytes(), agents)
        self.assertEqual((self.project / 'product.txt').read_bytes(), b'uncommitted product work')
        self.assertEqual(command(self.project, 'ls-files', '--stage'), index)

    def test_modified_core_prevents_apply_and_checkout(self):
        self.install(channel='edge')
        (self.project / uh.HOME / 'CORE.md').write_bytes(b'my core')
        self.update()
        before = files(self.project)
        with self.assertRaisesRegex(ValueError, 'Modified/missing managed file'):
            self.upgrade()
        self.assertEqual(files(self.project), before)
        self.assertEqual(command(self.module, 'rev-parse', 'HEAD'), self.old)

    def test_modified_bootstrap_is_not_overwritten(self):
        self.install(channel='edge')
        path = self.project / 'AGENTS.md'
        path.write_bytes(path.read_bytes().replace(b'Read ', b'Changed ', 1))
        before = files(self.project)
        with self.assertRaisesRegex(ValueError, 'managed block'):
            self.upgrade(offline=True)
        self.assertEqual(files(self.project), before)

    def test_modified_wrapper_or_state_blocks_apply(self):
        self.install(channel='edge')
        for name in (uh.HOME + '/harness', uh.STATE):
            path = self.project / name
            original = path.read_bytes()
            with self.subTest(path=name):
                path.write_bytes(original + b'\n')
                before = files(self.project)
                with self.assertRaises(ValueError):
                    self.upgrade(offline=True)
                self.assertEqual(files(self.project), before)
            path.write_bytes(original)

    def test_dirty_module_never_reset(self):
        self.install(channel='edge')
        (self.module / 'AGENTS.template.md').write_bytes(b'dirty module')
        self.update()
        with self.assertRaisesRegex(ValueError, 'local changes'):
            self.life.pull()
        with self.assertRaisesRegex(ValueError, 'local changes'):
            self.upgrade()
        self.assertEqual((self.module / 'AGENTS.template.md').read_bytes(), b'dirty module')

    def test_untracked_module_file_blocks_checkout(self):
        self.install(channel='edge')
        (self.module / 'notes.txt').write_bytes(b'notes')
        with self.assertRaisesRegex(ValueError, 'local changes'):
            self.life.pull()

    def test_source_origin_mismatch_is_not_silently_repaired(self):
        self.install(channel='edge')
        command(self.module, 'remote', 'set-url', 'origin', str(self.root / 'other'))
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            self.upgrade()
        self.assertEqual(command(self.module, 'remote', 'get-url', 'origin'), str(self.root / 'other'))

    def test_stable_has_no_implicit_main_fallback(self):
        self.install()
        with self.assertRaisesRegex(ValueError, 'No stable'):
            self.life.select(self.life.config())

    def test_stable_uses_numeric_semver_and_ignores_prereleases(self):
        self.install()
        command(self.source, 'tag', 'v3.9.0')
        new = self.update('3.10.0')
        command(self.source, 'tag', '-a', 'v3.10.0', '-m', 'release')
        command(self.source, 'tag', 'v9.0.0-beta.1')
        result = self.upgrade()
        self.assertEqual(result['applied_revision'], new)
        self.assertEqual(result['selection']['ref'], 'refs/tags/v3.10.0')

    def test_stable_tag_manifest_mismatch_fails_before_checkout(self):
        self.install()
        command(self.source, 'tag', 'v99.0.0')
        before = files(self.project)
        with self.assertRaisesRegex(ValueError, 'manifest version'):
            self.upgrade()
        self.assertEqual(files(self.project), before)
        self.assertEqual(command(self.module, 'rev-parse', 'HEAD'), self.old)

    def test_pinned_has_no_remote_discovery_and_does_not_follow_main(self):
        self.install(channel='pinned')
        self.update()
        with patch.object(uh, 'git', side_effect=AssertionError('unexpected discovery')):
            result = self.life.select(self.life.config())
        self.assertEqual(result['revision'], self.old)
        self.upgrade()
        self.assertEqual(self.life.lock()['applied_revision'], self.old)

    def test_explicit_ref_is_command_scoped_and_can_rollback(self):
        self.install(channel='edge')
        config = (self.project / uh.CONFIG).read_bytes()
        self.update()
        self.upgrade()
        self.upgrade(ref=self.old)
        self.assertEqual(self.life.lock()['applied_revision'], self.old)
        self.assertEqual((self.project / uh.CONFIG).read_bytes(), config)

    def test_ambiguous_or_option_ref_is_rejected(self):
        self.install(channel='edge')
        for ref in ('main', '-c', 'HEAD~1', 'refs/heads/../main'):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                self.life.select(self.life.config(), ref=ref)

    def test_moving_ref_between_discovery_and_fetch_does_not_apply(self):
        self.install(channel='edge')
        selected = self.life.select(self.life.config())
        self.update()
        with self.assertRaisesRegex(ValueError, 'moved during fetch'):
            self.life.fetch_candidate(selected)
        self.assertEqual(command(self.module, 'rev-parse', 'HEAD'), self.old)

    def test_missing_old_revision_is_explicit_diff_failure(self):
        self.install(channel='edge')
        lock = self.life.lock()
        lock['applied_revision'] = 'a' * 40
        (self.project / uh.LOCK).write_bytes(uh.encode(lock))
        with self.assertRaises(ValueError):
            self.life.diff()

    def test_obsolete_clean_skill_is_removed_but_user_file_is_preserved(self):
        self.install(channel='edge')
        meta = json.loads((self.source / 'harness.json').read_bytes())
        meta['skills'] = ['uh-new']
        path = self.source / 'skills/uh-new/SKILL.md'
        path.parent.mkdir(parents=True)
        path.write_bytes(b'---\nname: uh-new\ndescription: Fixture\n---\n')
        (self.source / 'harness.json').write_bytes(uh.encode(meta))
        new = self.commit_source('fixture: retire skill')
        old_folder = self.project / '.agents/skills/uh-debug'
        (old_folder / 'my-notes.txt').write_bytes(b'keep')
        self.upgrade()
        self.assertFalse((old_folder / 'SKILL.md').exists())
        self.assertEqual((old_folder / 'my-notes.txt').read_bytes(), b'keep')
        self.assertEqual(self.life.lock()['applied_revision'], new)

    def test_mid_write_failure_restores_files_and_source(self):
        self.install(channel='edge')
        self.update()
        before = files(self.project)
        original = uh.atomic_write
        count = [0]
        def fail_once(path, raw, mode=0o644):
            count[0] += 1
            if count[0] == 3:
                raise OSError('simulated write failure')
            return original(path, raw, mode)
        with patch.object(uh, 'atomic_write', side_effect=fail_once):
            with self.assertRaisesRegex(OSError, 'simulated'):
                self.upgrade()
        self.assertEqual(files(self.project), before)
        self.assertEqual(command(self.module, 'rev-parse', 'HEAD'), self.old)

    def test_post_verification_failure_restores_state_and_wrappers(self):
        self.install(channel='edge')
        self.update()
        before = files(self.project)
        with patch.object(self.life, 'verify', side_effect=ValueError('verify failed')):
            with self.assertRaisesRegex(ValueError, 'verify failed'):
                self.upgrade()
        self.assertEqual(files(self.project), before)
        self.assertEqual(command(self.module, 'rev-parse', 'HEAD'), self.old)

    def test_first_install_failure_removes_generated_files(self):
        before = files(self.project)
        with patch.object(self.life, 'verify', side_effect=ValueError('verify failed')):
            with self.assertRaises(ValueError):
                self.install(channel='edge')
        self.assertEqual(files(self.project), before)
        self.assertFalse((self.project / '.agents').exists())

    def test_recovery_refuses_to_overwrite_subsequent_edit(self):
        self.install(channel='edge')
        self.update()
        def fail(state):
            (self.project / uh.HOME / 'CORE.md').write_bytes(b'user changed after apply')
            raise ValueError('simulate external edit')
        with patch.object(self.life, 'verify', side_effect=fail):
            with self.assertRaisesRegex(ValueError, 'subsequent edit'):
                self.upgrade()
        self.assertTrue((self.project / uh.JOURNAL).exists())
        self.assertEqual((self.project / uh.HOME / 'CORE.md').read_bytes(), b'user changed after apply')
        with self.assertRaisesRegex(ValueError, 'Interrupted transaction'):
            self.life.pull()

    def test_crash_journal_can_be_recovered_explicitly(self):
        self.install(channel='edge')
        self.update()
        before = files(self.project)
        # SystemExit simulates a hard interruption outside ordinary rollback.
        with patch.object(self.life, 'verify', side_effect=SystemExit(123)):
            with self.assertRaises(SystemExit):
                self.upgrade()
        self.assertTrue(self.life.status()['recovery_required'])
        result = self.life.recover()
        self.assertTrue(result['recovered'])
        self.assertEqual(files(self.project), before)
        self.assertEqual(command(self.module, 'rev-parse', 'HEAD'), self.old)

    def test_mutex_blocks_parallel_mutation_without_deleting_lock(self):
        self.install(channel='edge')
        (self.project / uh.MUTEX).mkdir()
        with self.assertRaisesRegex(ValueError, 'Another lifecycle'):
            self.upgrade(offline=True)
        self.assertTrue((self.project / uh.MUTEX).is_dir())

    def test_tampered_journal_traversal_is_rejected(self):
        self.install(channel='edge')
        data = {'schema_version': 1, 'old_revision': self.old, 'new_revision': self.old,
                'files': {'../outside': {'before': None, 'mode': None, 'after': None}}}
        (self.project / uh.JOURNAL).write_bytes(uh.encode(data))
        with self.assertRaisesRegex(ValueError, 'Unsafe recovery'):
            self.life.recover()
        self.assertTrue((self.project / uh.JOURNAL).exists())

    def test_module_without_init_is_not_misidentified_as_parent_repo(self):
        self.install(channel='edge')
        command(self.project, 'submodule', 'deinit', '-f', '--', uh.MODULE)
        result = self.life.status()
        self.assertFalse(result['initialized'])
        self.assertIn('uninitialized', result['module_error'])
        self.assertEqual(result['applied_revision'], self.old)
        wrapper = self.wrapper('status')
        self.assertEqual(wrapper.returncode, 0, wrapper.stderr)

    def test_git_environment_does_not_redirect_parent_repo(self):
        self.install(channel='edge')
        with patch.dict(os.environ, {'GIT_DIR': str(self.source / '.git'),
                                     'GIT_WORK_TREE': str(self.source)}):
            self.assertEqual(self.life.status()['source_revision'], self.old)

    def test_newer_source_runtime_is_not_executed_by_pull_or_status(self):
        self.install(channel='edge')
        (self.source / 'scripts/harness.py').write_bytes(b'raise RuntimeError("candidate must not run")\n')
        self.commit_source('fixture: candidate runtime not activated')
        self.life.pull()
        result = self.wrapper('status')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['source_not_applied'])

    def test_symlink_target_file_is_not_followed(self):
        self.install(channel='edge')
        target = self.project / uh.HOME / 'CORE.md'
        outside = self.root / 'outside'
        target.rename(outside)
        try:
            target.symlink_to(outside)
        except OSError:
            self.skipTest('Symlinks unavailable')
        before = outside.read_bytes()
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.upgrade(offline=True)
        self.assertEqual(outside.read_bytes(), before)

    def test_unmanaged_wrapper_collision_is_not_overwritten(self):
        (self.project / uh.HOME / 'harness').write_bytes(b'user wrapper')
        before = files(self.project)
        with self.assertRaisesRegex(ValueError, 'Unmanaged lifecycle file'):
            self.install(channel='edge')
        self.assertEqual(files(self.project), before)

    def test_bad_config_and_credential_url_are_rejected(self):
        self.install(channel='edge')
        for change in ({'channel': 'latest'}, {'profile': 'missing'}, {'schema_version': 99},
                       {'source': 'https://token@github.com/owner/repo.git'}):
            config = self.life.config()
            (self.project / uh.CONFIG).write_bytes(uh.encode({**config, **change}))
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.life.config()
            (self.project / uh.CONFIG).write_bytes(uh.encode(config))

    def test_doctor_forwards_strict_exit_code(self):
        self.install(channel='edge')
        path = self.project / uh.HOME / 'tooling.py'
        path.write_bytes(b'import sys\nprint("fixture doctor")\nsys.exit(1 if "--strict" in sys.argv else 0)\n')
        result = self.wrapper('doctor', '--strict')
        self.assertEqual(result.returncode, 1)
        self.assertIn(b'fixture doctor', result.stdout)



    def test_legacy_proposal_is_preserved_during_explicit_migration(self):
        proposal = self.project / uh.HOME / 'AGENTS.proposed.md'
        proposal.write_bytes(b'legacy proposal; preserve this')
        state = {'schema_version': 2, 'core_status': 'manual_merge_required',
                 'files': {uh.HOME + '/AGENTS.proposed.md': uh.digest(proposal.read_bytes())}}
        (self.project / uh.STATE).write_bytes(uh.encode(state))
        agents = self.project / 'AGENTS.md'
        agents.write_bytes(agents.read_bytes() + b'\n' + (self.source / 'AGENTS.bootstrap.md').read_bytes())
        self.install(channel='edge', adopt=True)
        self.assertEqual(proposal.read_bytes(), b'legacy proposal; preserve this')
        self.assertNotIn(uh.HOME + '/AGENTS.proposed.md', json.loads((self.project / uh.STATE).read_bytes())['files'])

    def test_full_distribution_installs_all_skills_when_available(self):
        if not (ROOT / 'harness.json').is_file():
            self.skipTest('Partial local source; complete-distribution test is required in repository CI')
        meta = json.loads((ROOT / 'harness.json').read_bytes())
        sources = ['harness.json', 'AGENTS.template.md', 'AGENTS.bootstrap.md', 'scripts/install.py',
                   *meta.get('support_files', {}).values(),
                   *['profiles/' + p + '.md' for p in meta['profiles']],
                   *['skills/' + s + '/SKILL.md' for s in meta['skills']]]
        for name in sources:
            dest = self.source / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dest)
        new = self.commit_source('fixture: full distribution')
        command(self.module, 'fetch', 'origin', 'main')
        command(self.module, 'checkout', '--detach', new)
        self.install(channel='edge')
        actual = {p.parent.name for p in (self.project / '.agents/skills').glob('*/SKILL.md')}
        self.assertEqual(actual, set(meta['skills']))
        self.assertEqual(self.life.integrity(), [])
        result = self.wrapper('doctor', '--global-skill-root', str(self.root / 'empty-global'), '--strict')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_source_url_rejects_query_credentials_and_remote_helpers(self):
        for value in ('https://github.com/r.git?token=secret', 'ext::sh -c run', 'file://remote/path'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                uh.source_url(value)

    def test_case_aliases_of_lifecycle_files_are_not_payload(self):
        for name in ('module.JSON', 'CONFIG.JSON', 'Lifecycle.py', 'module', 'AGENTS.proposed.md'):
            self.assertFalse(uh.allowed_payload(uh.HOME + '/' + name))



    def test_offline_does_not_silently_ignore_explicit_ref(self):
        self.install(channel='edge')
        with self.assertRaisesRegex(ValueError, 'offline uses'):
            self.upgrade(offline=True, ref=self.old)

    def test_config_profile_change_is_applied_without_overwriting_config(self):
        self.install(channel='edge')
        config = self.life.config()
        config['profile'] = 'sol'
        raw = uh.encode(config)
        (self.project / uh.CONFIG).write_bytes(raw)
        self.upgrade(offline=True)
        self.assertEqual(self.life.lock()['profile'], 'sol')
        self.assertEqual((self.project / uh.CONFIG).read_bytes(), raw)

    def test_syntax_invalid_candidate_runtime_fails_before_checkout(self):
        self.install(channel='edge')
        (self.source / 'scripts/harness.py').write_bytes(b'def broken(\n')
        self.commit_source('fixture: invalid candidate')
        before = files(self.project)
        with self.assertRaisesRegex(ValueError, 'invalid Python syntax'):
            self.upgrade()
        self.assertEqual(files(self.project), before)
        self.assertEqual(command(self.module, 'rev-parse', 'HEAD'), self.old)

    def test_stable_does_not_implicitly_downgrade(self):
        self.install(channel='edge')
        self.update('3.10.0')
        self.upgrade()
        command(self.source, 'tag', 'v3.0.0', self.old)
        before = files(self.project)
        with self.assertRaisesRegex(ValueError, 'older than'):
            self.upgrade(channel='stable')
        self.assertEqual(files(self.project), before)


class LifecyclePackageTests(unittest.TestCase):
    def test_behavior_cases_are_scenarios_not_execution_evidence(self):
        data = json.loads((ROOT / 'evals/lifecycle-cases.json').read_bytes())
        self.assertEqual(data['kind'], 'behavioral_scenarios_not_execution_results')
        self.assertEqual(len(data['cases']), 8)
        self.assertEqual(len({c['id'] for c in data['cases']}), 8)
        for case in data['cases']:
            for key in ('prompt', 'required', 'forbidden'):
                self.assertTrue(case[key])

    def test_wrapper_and_runtime_are_shipped_together(self):
        for name in uh.EXTRAS.values():
            self.assertTrue((ROOT / name).is_file(), name)
        wrapper = (ROOT / 'scripts/harness').read_text()
        self.assertIn('lifecycle.py', wrapper)
        self.assertNotIn('module/scripts', wrapper)
        self.assertIn('--project', wrapper)
        self.assertTrue((ROOT / 'docs/LIFECYCLE.md').is_file())


if __name__ == '__main__':
    unittest.main()
