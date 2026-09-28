"""Deterministic tooling tests; no provider/model/network calls or real user config."""
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
import tooling
import install as installer


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*')
            if p.is_file() and not p.is_symlink()}


def make_skill(root, folder, name, extra=''):
    path = root / folder / 'SKILL.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'---\nname: {name}\ndescription: Test fixture\n---\n{extra}', encoding='utf-8')
    return path


class ToolingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.project = self.root / 'project with spaces'
        self.project.mkdir()
        self.global_root = self.root / 'global skills'
        self.global_root.mkdir()
        self.local = self.project / '.agents/skills'
        self.catalog = tooling.load_catalog(ROOT / 'integrations/tooling.json')

    def scan(self):
        return tooling.scan_skills(tooling.skill_roots(self.project, [self.global_root]))

    def report(self, available=(), executables=()):
        with patch.object(tooling.shutil, 'which', side_effect=lambda x: '/fake/' + x if x in executables else None):
            return tooling.inventory(self.project, self.catalog, [self.global_root], available)

    def test_catalog_has_complete_routes(self):
        self.assertEqual(set(self.catalog['capabilities']), {
            'discover', 'author-skill', 'library-docs', 'symbols', 'architecture',
            'browser-check', 'browser-debug', 'repository', 'independent-review',
            'security-review', 'production-debug', 'human-diagrams',
        })
        for spec in self.catalog['capabilities'].values():
            self.assertTrue(spec['fallback'])
            self.assertTrue(spec['checks'])

    def test_invalid_catalogs_are_rejected(self):
        mutations = [lambda x: x.update(schema_version=9),
                     lambda x: x['providers']['serena'].update(executables=['../run']),
                     lambda x: x['capabilities']['symbols'].update(providers=['unknown']),
                     lambda x: x['capabilities']['symbols'].update(fallback=''),
                     lambda x: x['capabilities']['symbols'].update(checks=[])]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                obj = copy.deepcopy(self.catalog)
                mutate(obj)
                path = self.root / 'invalid.json'
                path.write_text(json.dumps(obj), encoding='utf-8')
                with self.assertRaises(ValueError):
                    tooling.load_catalog(path)

    def test_names_come_from_frontmatter_not_folder(self):
        make_skill(self.global_root, 'renamed-folder', 'find-docs')
        self.assertEqual(self.scan()['skills'][0]['name'], 'find-docs')

    def test_quoted_name_crlf_bom(self):
        raw = b'\xef\xbb\xbf---\r\nname: "find-docs" # comment\r\ndescription: test\r\n---\r\n'
        self.assertEqual(tooling.skill_name(raw), 'find-docs')

    def test_invalid_frontmatter_is_not_guessed(self):
        for raw in (b'name: demo', b'---\nname: one\nname: two\n---\n', b'---\nname: |\n  demo\n---\n'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                tooling.skill_name(raw)

    def test_identical_duplicate_is_reported_and_untouched(self):
        make_skill(self.global_root, 'find-docs', 'find-docs')
        make_skill(self.local, 'different-folder', 'find-docs')
        before = snapshot(self.root)
        self.assertEqual(self.scan()['duplicates'][0]['kind'], 'same_skill_md')
        self.assertEqual(before, snapshot(self.root))

    def test_different_duplicate_is_reported(self):
        make_skill(self.global_root, 'find-docs', 'find-docs', 'global')
        make_skill(self.local, 'find-docs', 'find-docs', 'local')
        self.assertEqual(self.scan()['duplicates'][0]['kind'], 'different_skill_md')

    def test_symlink_alias_is_reported(self):
        original = make_skill(self.global_root, 'find-docs', 'find-docs')
        self.local.mkdir(parents=True)
        try:
            (self.local / 'alias').symlink_to(original.parent, target_is_directory=True)
        except OSError:
            self.skipTest('Symlinks unavailable')
        self.assertEqual(self.scan()['duplicates'][0]['kind'], 'alias')

    def test_symlink_loop_terminates(self):
        make_skill(self.global_root, 'find-docs', 'find-docs')
        try:
            (self.global_root / 'loop').symlink_to(self.global_root, target_is_directory=True)
        except OSError:
            self.skipTest('Symlinks unavailable')
        self.assertLess(len(self.scan()['skills']), 5)

    def test_same_root_argument_is_not_false_duplicate(self):
        make_skill(self.global_root, 'find-docs', 'find-docs')
        roots = tooling.skill_roots(self.project, [self.global_root, self.global_root])
        self.assertEqual(tooling.scan_skills(roots)['duplicates'], [])

    def test_nested_repo_scopes_stop_at_git_worktree(self):
        (self.project / '.git').write_text('gitdir: /not-read', encoding='utf-8')
        nested = self.project / 'app/sub'
        nested.mkdir(parents=True)
        roots = tooling.skill_roots(nested, [])
        self.assertEqual([p for _, p in roots], [nested / '.agents/skills', nested.parent / '.agents/skills', self.local])

    def test_non_git_project_does_not_scan_home_ancestors(self):
        self.assertEqual(tooling.skill_roots(self.project, []), [('repo', self.local)])

    def test_skill_only_is_not_executable(self):
        make_skill(self.global_root, 'playwright-cli', 'playwright-cli')
        result = self.report()
        self.assertEqual(result['providers']['playwright']['status'], 'instructions_only')
        self.assertIsNone(tooling.route('browser-check', self.catalog, result)['candidate'])

    def test_mcp_binary_is_not_active_mcp(self):
        result = self.report(executables=('serena',))
        self.assertEqual(result['providers']['serena']['status'], 'runtime_unverified')
        self.assertIsNone(tooling.route('symbols', self.catalog, result)['candidate'])

    def test_host_report_is_not_authentication(self):
        result = self.report(available=('serena',))
        route = tooling.route('symbols', self.catalog, result)
        self.assertEqual(route['candidate'], 'serena')
        self.assertEqual(route['readiness'], 'unverified')
        self.assertEqual(route['authorization'], 'not_granted_by_report')

    def test_unknown_host_report_is_rejected(self):
        with self.assertRaises(ValueError):
            self.report(available=('not-a-provider',))

    def test_cli_candidate_does_not_require_duplicate_skill_copy(self):
        result = self.report(executables=('ctx7',))
        self.assertEqual(tooling.route('library-docs', self.catalog, result)['candidate'], 'context7')
        self.assertFalse(self.local.exists())

    def test_npx_alone_does_not_establish_find_skills(self):
        result = self.report(executables=('npx',))
        self.assertIsNone(tooling.route('discover', self.catalog, result)['candidate'])

    def test_ambiguous_skill_is_not_selected_even_when_reported(self):
        make_skill(self.global_root, 'find-docs', 'find-docs')
        make_skill(self.local, 'find-docs', 'find-docs')
        result = self.report(available=('context7',), executables=('ctx7',))
        self.assertIsNone(tooling.route('library-docs', self.catalog, result)['candidate'])

    def test_offline_excludes_network_candidate(self):
        result = self.report(executables=('ctx7',))
        self.assertIsNone(tooling.route('library-docs', self.catalog, result, offline=True)['candidate'])

    def test_browser_selection_does_not_mandate_two_tools(self):
        result = self.report(available=('chrome-devtools',), executables=('playwright-cli',))
        self.assertEqual(tooling.route('browser-check', self.catalog, result)['candidate'], 'playwright')
        self.assertEqual(tooling.route('browser-debug', self.catalog, result)['candidate'], 'chrome-devtools')

    def test_missing_tools_have_explicit_fallback(self):
        report = self.report()
        for name in self.catalog['capabilities']:
            result = tooling.route(name, self.catalog, report)
            self.assertIsNone(result['candidate'])
            self.assertTrue(result['fallback'])

    def test_oversized_definition_warns_and_blocks_advisory_selection(self):
        path = make_skill(self.global_root, 'broken', 'broken', 'x' * tooling.MAX_BYTES)
        report = self.report(executables=('ctx7',))
        self.assertTrue(report['warnings'])
        self.assertIsNone(tooling.route('library-docs', self.catalog, report)['candidate'])
        self.assertTrue(path.exists())

    def test_scan_budget_is_visible(self):
        make_skill(self.global_root, 'demo', 'demo')
        with patch.object(tooling, 'MAX_DIRS', 0):
            self.assertTrue(self.scan()['warnings'])

    def test_no_provider_commands_or_network_are_run(self):
        before = snapshot(self.root)
        with patch('subprocess.run', side_effect=AssertionError('unexpected command')), \
             patch('socket.create_connection', side_effect=AssertionError('unexpected network')):
            result = self.report(available=('github', 'codex-security'))
            tooling.route('repository', self.catalog, result)
        self.assertEqual(before, snapshot(self.root))

    def test_cli_json_and_strict_exit(self):
        make_skill(self.global_root, 'find-docs', 'find-docs')
        make_skill(self.local, 'find-docs', 'find-docs')
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/tooling.py'), 'doctor',
                                 str(self.project), '--global-skill-root', str(self.global_root), '--strict'],
                                text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)['duplicates'][0]['name'], 'find-docs')

    def test_cli_invalid_provider_exits_two(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/tooling.py'), 'doctor',
                                 str(self.project), '--no-global-skills', '--available', 'unknown'],
                                text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)


class ToolingInstallTests(unittest.TestCase):
    """Minimal distribution fixtures exercise installer transitions, not model behavior."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.package = self.root / 'package'
        self.target = self.root / 'target'
        self.global_root = self.root / 'global'
        self.target.mkdir()
        self.global_root.mkdir()
        self.package.mkdir()
        self.meta = json.loads((ROOT / 'harness.json').read_text(encoding='utf-8'))
        self.write_meta()
        for path in ('AGENTS.template.md', 'AGENTS.bootstrap.md', 'scripts/tooling.py', 'integrations/tooling.json', 'docs/TOOLING.md'):
            dest = self.package / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, dest)
        for name in self.meta['skills']:
            make_skill(self.package / 'skills', name, name)
        for name in self.meta['profiles']:
            dest = self.package / 'profiles' / (name + '.md')
            dest.parent.mkdir(exist_ok=True)
            dest.write_text('# ' + name, encoding='utf-8')
        self.root_patch = patch.object(installer, 'ROOT', self.package)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def write_meta(self):
        (self.package / 'harness.json').write_text(json.dumps(self.meta), encoding='utf-8')

    def install(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return installer.install(self.target, 'generic', global_skill_roots=[self.global_root], **kwargs)

    def test_support_files_installed_and_hash_managed(self):
        state = self.install()
        for dest, source in self.meta['support_files'].items():
            self.assertEqual((self.target / dest).read_bytes(), (self.package / source).read_bytes())
            self.assertEqual(state['files'][dest], installer.digest((self.target / dest).read_bytes()))
        self.assertEqual(snapshot(self.global_root), {})

    def test_support_install_is_idempotent(self):
        self.install()
        before = snapshot(self.target)
        self.install()
        self.assertEqual(before, snapshot(self.target))

    def test_dry_run_writes_nothing(self):
        self.install(dry_run=True)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_installed_doctor_works_without_source_tree(self):
        self.install()
        shutil.rmtree(self.package)
        result = subprocess.run([sys.executable, str(self.target / '.universal-harness/tooling.py'),
                                 'doctor', str(self.target), '--no-global-skills', '--strict'],
                                cwd=self.target, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(result.stdout)['skills']), len(self.meta['skills']))

    def test_managed_v2_state_migrates_to_block_ownership(self):
        self.install()
        state_path = self.target / installer.STATE
        state = json.loads(state_path.read_text())
        for relative in [*self.meta['support_files'], '.agents/skills/uh-tooling/SKILL.md']:
            (self.target / relative).unlink()
            state['files'].pop(relative)
        core = self.target / 'AGENTS.md'
        core.write_text('# Old managed core', encoding='utf-8')
        state['files']['AGENTS.md'] = installer.digest(core.read_bytes())
        state['version'] = '2.0.2'
        state['schema_version'] = 2
        state.pop('agents')
        state['core_status'] = 'managed'
        (self.target / installer.CORE).unlink()
        state['files'].pop(installer.CORE)
        state_path.write_text(json.dumps(state), encoding='utf-8')
        upgraded = self.install(upgrade=True)
        self.assertEqual(upgraded['schema_version'], 3)
        self.assertNotIn('AGENTS.md', upgraded['files'])
        self.assertIn(installer.CORE, upgraded['files'])
        self.assertEqual(upgraded['version'], '3.0.0')
        self.assertTrue((self.target / '.universal-harness/tooling.py').exists())

    def test_modified_support_blocks_all_upgrade_writes(self):
        self.install()
        (self.target / '.universal-harness/tooling.json').write_text('user data', encoding='utf-8')
        before = snapshot(self.target)
        with self.assertRaises(ValueError):
            self.install(upgrade=True)
        self.assertEqual(before, snapshot(self.target))

    def test_global_same_name_blocks_before_writes(self):
        make_skill(self.global_root, 'different-folder', 'uh-tooling')
        before = snapshot(self.root)
        with self.assertRaisesRegex(ValueError, 'same-name skills'):
            self.install()
        self.assertEqual(before, snapshot(self.root))

    def test_upper_repo_same_name_blocks_before_writes(self):
        (self.root / '.git').mkdir()
        make_skill(self.root / '.agents/skills', 'uh-tooling', 'uh-tooling')
        with self.assertRaisesRegex(ValueError, 'same-name skills'):
            self.install()
        self.assertEqual(list(self.target.iterdir()), [])

    def test_third_party_skills_are_not_copied_or_removed(self):
        source = make_skill(self.global_root, 'find-docs', 'find-docs')
        before = source.read_bytes()
        self.install()
        self.assertEqual(source.read_bytes(), before)
        self.assertFalse((self.target / '.agents/skills/find-docs').exists())

    def test_missing_support_is_preflighted(self):
        (self.package / 'scripts/tooling.py').unlink()
        with self.assertRaisesRegex(ValueError, 'Incomplete harness source package'):
            self.install()
        self.assertEqual(list(self.target.iterdir()), [])

    def test_unsafe_support_mappings_are_rejected(self):
        cases = [('../outside', 'docs/TOOLING.md'),
                 ('.universal-harness/STATE.json', 'docs/TOOLING.md'),
                 ('.universal-harness/state.JSON', 'docs/TOOLING.md'),
                 ('.universal-harness/extra.md', '../outside'),
                 ('.universal-harness/extra.md', 'docs\\..\\outside')]
        for destination, source in cases:
            with self.subTest(destination=destination, source=source):
                self.meta['support_files'] = {destination: source}
                self.write_meta()
                with self.assertRaises(ValueError):
                    self.install()
                self.assertEqual(list(self.target.iterdir()), [])

    def test_support_source_symlink_is_refused(self):
        path = self.package / 'docs/TOOLING.md'
        saved = self.root / 'outside.md'
        path.rename(saved)
        try:
            path.symlink_to(saved)
        except OSError:
            self.skipTest('Symlinks unavailable')
        with self.assertRaisesRegex(ValueError, 'Symlink source refused'):
            self.install()
        self.assertEqual(list(self.target.iterdir()), [])


class ToolingPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('harness.json', 'scripts/tooling.py', 'docs/TOOLING.md',
                     'integrations/tooling.json', 'evals/tooling-cases.json'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, path)

    def mutate(self, path, operation):
        target = self.root / path
        value = json.loads(target.read_text(encoding='utf-8'))
        operation(value)
        target.write_text(json.dumps(value), encoding='utf-8')

    def test_complete_tooling_package(self):
        self.assertEqual(tooling.validate_package(self.root), [])

    def test_missing_support_mapping_is_rejected(self):
        self.mutate('harness.json', lambda x: x.pop('support_files'))
        self.assertIn('Tooling support file mapping mismatch', tooling.validate_package(self.root))

    def test_missing_support_source_is_rejected(self):
        (self.root / 'scripts/tooling.py').unlink()
        self.assertIn('Missing tooling support source: scripts/tooling.py', tooling.validate_package(self.root))

    def test_missing_route_is_rejected(self):
        self.mutate('integrations/tooling.json', lambda x: x['capabilities'].pop('architecture'))
        self.assertIn('Missing tooling capability routes', tooling.validate_package(self.root))

    def test_missing_eval_is_rejected(self):
        self.mutate('evals/tooling-cases.json', lambda x: x['cases'].pop())
        self.assertIn('Missing or duplicated tooling eval IDs', tooling.validate_package(self.root))

    def test_global_mutation_contract_cannot_be_enabled(self):
        self.mutate('harness.json', lambda x: x.update(runtime_configuration_managed=True))
        self.assertIn('Tooling must not own global runtime or upstream plugins', tooling.validate_package(self.root))


if __name__ == '__main__':
    unittest.main()
