"""Package/routing contracts only; no model, renderer or human comprehension claim."""
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
NEW_SKILLS = {'uh-developer-context-sync', 'uh-human-diagramming'}
CASE_IDS = {
    'human-onboard-empty', 'human-catch-up-known-base', 'human-catch-up-no-base',
    'human-diverged-base', 'human-shallow-history', 'human-reader-and-scope',
    'human-dirty-tree', 'human-doc-code-drift', 'human-checkpoint-acknowledgement',
    'human-sensitive-checkpoint', 'human-semantic-fixture-change',
    'human-diagram-evidence', 'human-renderer-absent', 'human-renderer-failure',
    'human-untrusted-diagram', 'human-diagram-budget', 'human-deep-dive',
    'human-not-automatic', 'human-independent-diagram',
}


class HumanContextContractTests(unittest.TestCase):
    def setUp(self):
        self.meta = json.loads((ROOT / 'harness.json').read_text(encoding='utf-8'))
        self.catalog = json.loads((ROOT / 'integrations/tooling.json').read_text(encoding='utf-8'))

    def test_new_skills_are_in_installer_inventory_once(self):
        for name in NEW_SKILLS:
            self.assertEqual(self.meta['skills'].count(name), 1)
            self.assertTrue((ROOT / 'skills' / name / 'SKILL.md').is_file())
        self.assertEqual(len(self.meta['skills']), len(set(self.meta['skills'])))

    def test_self_contained_skill_frontmatter_and_budget(self):
        for name in NEW_SKILLS:
            with self.subTest(skill=name):
                path = ROOT / 'skills' / name / 'SKILL.md'
                raw = path.read_bytes()
                header = re.match(r'\A---\nname: ([a-z0-9-]+)\ndescription: ([^\n]+)\n---\n', raw.decode('utf-8'))
                self.assertIsNotNone(header)
                self.assertEqual(header[1], name)
                self.assertLessEqual(len(header[2]), 1024)
                self.assertLessEqual(len(raw), self.meta['limits']['skill_bytes'])
                # Installed SKILL.md must not depend on source-only relative files.
                self.assertEqual(re.findall(r'\]\((?![a-z]+:|#)([^)\s]+)\)', raw.decode('utf-8')), [])

    def test_opt_in_core_triggers_fit_existing_budget(self):
        core = (ROOT / self.meta['core']).read_bytes()
        self.assertLessEqual(len(core), self.meta['limits']['core_bytes'])
        for name in NEW_SKILLS:
            self.assertIn(f'`{name}`:'.encode(), core)

    def test_renderer_is_a_cli_capability_not_a_bundled_runtime(self):
        self.assertEqual(self.catalog['providers']['mermaid-cli'], {
            'kind': 'cli', 'skills': [], 'executables': ['mmdc'], 'network': False,
        })
        spec = self.catalog['capabilities']['human-diagrams']
        self.assertEqual(spec['providers'], ['mermaid-cli'])
        self.assertTrue(spec['fallback'])
        self.assertTrue(spec['checks'])
        self.assertFalse(self.meta['runtime_configuration_managed'])
        self.assertFalse(self.meta['upstream_plugins_vendored'])

    def test_human_cases_have_an_explicit_manifest_path(self):
        self.assertEqual(self.meta['human_context_evaluation_cases'], 'evals/human-context-cases.json')
        self.assertTrue((ROOT / self.meta['human_context_evaluation_cases']).is_file())

    def test_case_inventory_and_evidence_kind(self):
        cases = json.loads((ROOT / self.meta['human_context_evaluation_cases']).read_text(encoding='utf-8'))
        self.assertEqual(cases['schema_version'], 2)
        self.assertEqual(cases['kind'], 'behavioral_scenarios_not_execution_results')
        ids = [case['id'] for case in cases['cases']]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), CASE_IDS)

    def test_cases_have_nonempty_acceptance_and_forbidden_behaviors(self):
        cases = json.loads((ROOT / self.meta['human_context_evaluation_cases']).read_text(encoding='utf-8'))
        for case in cases['cases']:
            with self.subTest(case=case['id']):
                self.assertIsInstance(case['prompt'], str)
                self.assertTrue(case['prompt'].strip())
                for key in ('required', 'forbidden'):
                    self.assertIsInstance(case[key], list)
                    self.assertTrue(case[key])
                    self.assertTrue(all(isinstance(item, str) and item.strip() for item in case[key]))

    def test_guide_relative_links_resolve(self):
        guide = ROOT / 'docs/HUMAN-CONTEXT.md'
        self.assertTrue(guide.is_file())
        for target in re.findall(r'\]\(([^)\s]+)\)', guide.read_text(encoding='utf-8')):
            if re.match(r'^[a-z]+:', target) or target.startswith('#'):
                continue
            self.assertTrue((guide.parent / target.split('#', 1)[0]).exists(), target)

    def test_no_behavioral_certification_is_added(self):
        self.assertEqual(self.meta['behavioral_validation'], {'sol': 'not_run', 'astra': 'not_run'})


class HumanDiagramRouteTests(unittest.TestCase):
    def setUp(self):
        # Import the actual shipped router; never substitute a fake implementation.
        sys.path.insert(0, str(ROOT / 'scripts'))
        import tooling
        self.tooling = tooling
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name).resolve()
        self.catalog = tooling.load_catalog(ROOT / 'integrations/tooling.json')

    def report(self, executables=()):
        with patch.object(self.tooling.shutil, 'which',
                          side_effect=lambda name: '/observed/' + name if name in executables else None):
            return self.tooling.inventory(self.project, self.catalog, global_roots=[])

    def test_missing_renderer_has_no_candidate(self):
        route = self.tooling.route('human-diagrams', self.catalog, self.report(), offline=True)
        self.assertIsNone(route['candidate'])
        self.assertIn('NOT RUN', route['fallback'])
        self.assertEqual(list(self.project.iterdir()), [])

    def test_local_renderer_is_advisory_not_verified(self):
        route = self.tooling.route('human-diagrams', self.catalog, self.report(('mmdc',)), offline=True)
        self.assertEqual(route['candidate'], 'mermaid-cli')
        self.assertEqual(route['readiness'], 'unverified')
        self.assertEqual(route['authorization'], 'not_granted_by_report')

    def test_npx_or_graphify_is_not_a_mermaid_renderer(self):
        report = self.report(('npx', 'graphify'))
        self.assertIsNone(self.tooling.route('human-diagrams', self.catalog, report)['candidate'])
        self.assertEqual(self.tooling.route('architecture', self.catalog, report)['candidate'], 'graphify')

    def test_route_does_not_render_install_or_use_network(self):
        with patch('subprocess.run', side_effect=AssertionError('unexpected renderer/install')), \
             patch('socket.create_connection', side_effect=AssertionError('unexpected network')):
            route = self.tooling.route('human-diagrams', self.catalog, self.report(('mmdc',)), offline=True)
        self.assertEqual(route['candidate'], 'mermaid-cli')
        self.assertEqual(list(self.project.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
