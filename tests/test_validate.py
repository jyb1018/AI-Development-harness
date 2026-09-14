import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import validate


class ValidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'package'
        shutil.copytree(validate.ROOT, self.root,
                        ignore=shutil.ignore_patterns('.git', '__pycache__', '.local'))

    def test_package(self):
        self.assertEqual(validate.validate(self.root), [])

    def test_missing_file(self):
        (self.root / 'VERSION').unlink()
        self.assertIn('Missing: VERSION', validate.validate(self.root))

    def test_version_mismatch(self):
        (self.root / 'VERSION').write_text('0.0.0', encoding='utf-8')
        self.assertIn('Version mismatch', validate.validate(self.root))

    def test_broken_link(self):
        with (self.root / 'README.md').open('a', encoding='utf-8') as f:
            f.write('\n[missing](missing.md)\n')
        self.assertTrue(any('Broken file link' in s for s in validate.validate(self.root)))

    def test_invalid_frontmatter(self):
        (self.root / 'skills/uh-debug/SKILL.md').write_text('no metadata', encoding='utf-8')
        self.assertIn('Invalid skill frontmatter: uh-debug', validate.validate(self.root))

    def test_missing_skill_source(self):
        (self.root / 'skills/uh-debug/SKILL.md').unlink()
        self.assertIn('Missing skill source: skills/uh-debug/SKILL.md',
                      validate.validate(self.root))

    def test_budget_limit(self):
        (self.root / 'AGENTS.template.md').write_text('x' * 6501, encoding='utf-8')
        self.assertIn('Core exceeds instruction budget', validate.validate(self.root))

    def test_duplicate_eval(self):
        path = self.root / 'evals/cases.json'
        obj = json.loads(path.read_text())
        obj['cases'].append(obj['cases'][0])
        path.write_text(json.dumps(obj), encoding='utf-8')
        self.assertIn('Empty or duplicated eval IDs', validate.validate(self.root))


if __name__ == '__main__':
    unittest.main()
