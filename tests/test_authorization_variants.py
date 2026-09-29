"""Scenario/validator regressions only; no Guardian or paid model execution."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import validate


def authorization_case(root):
    catalog = json.loads((root / 'evals/cases.json').read_text(encoding='utf-8'))
    return next(case for case in catalog['cases'] if case['id'] == 'host-authorization-revision')


class AuthorizationVariantTests(unittest.TestCase):
    def setUp(self):
        self.case = {'variants': [
            {'id': name, 'prompt': 'controlled fixture',
             'required': ['observe the boundary'], 'forbidden': ['bypass approval'],
             'expected_effect_count': count}
            for name, count in [('authorization-revoked', 0), ('status-only-update', 1)]
        ]}

    def test_catalog_contains_both_variants(self):
        self.assertEqual(validate.validate_authorization_variants(authorization_case(validate.ROOT)), [])

    def test_valid_contract(self):
        original = copy.deepcopy(self.case)
        self.assertEqual(validate.validate_authorization_variants(self.case), [])
        self.assertEqual(self.case, original)

    def test_each_variant_is_required(self):
        for name in ('authorization-revoked', 'status-only-update'):
            with self.subTest(name=name):
                case = copy.deepcopy(self.case)
                case['variants'] = [v for v in case['variants'] if v['id'] != name]
                self.assertIn('Missing authorization variants: ' + name,
                              validate.validate_authorization_variants(case))

    def test_missing_or_malformed_variant_collection(self):
        self.assertTrue(validate.validate_authorization_variants({}))
        for value in (None, [], {}, 'status-only-update', True):
            with self.subTest(value=value):
                self.assertTrue(validate.validate_authorization_variants({'variants': value}))

    def test_non_object_variant(self):
        for value in (None, [], 'status-only-update', 1):
            with self.subTest(value=value):
                case = copy.deepcopy(self.case)
                case['variants'].append(value)
                self.assertIn('Invalid authorization variant: expected object',
                              validate.validate_authorization_variants(case))

    def test_invalid_or_duplicate_variant_id(self):
        for value in (None, '', ' ', [], True):
            with self.subTest(value=value):
                case = copy.deepcopy(self.case)
                case['variants'][0]['id'] = value
                self.assertIn('Invalid authorization variant ID',
                              validate.validate_authorization_variants(case))
        self.case['variants'].append(copy.deepcopy(self.case['variants'][1]))
        self.assertIn('Duplicate authorization variant ID: status-only-update',
                      validate.validate_authorization_variants(self.case))

    def test_effect_count_contract(self):
        for index, wrong_count in ((0, 1), (1, 0), (1, 2)):
            with self.subTest(index=index, count=wrong_count):
                case = copy.deepcopy(self.case)
                variant = case['variants'][index]
                variant['expected_effect_count'] = wrong_count
                self.assertIn('Unexpected authorization variant effect count: ' + variant['id'],
                              validate.validate_authorization_variants(case))

    def test_effect_count_rejects_missing_and_non_integer_values(self):
        for value in (None, True, False, '1', 1.0, -1, [], {}):
            with self.subTest(value=value):
                case = copy.deepcopy(self.case)
                case['variants'][1]['expected_effect_count'] = value
                self.assertIn('Invalid authorization variant effect count: status-only-update',
                              validate.validate_authorization_variants(case))
        del self.case['variants'][1]['expected_effect_count']
        self.assertTrue(validate.validate_authorization_variants(self.case))

    def test_prompt_and_rubrics_are_nonempty_text(self):
        for field, values in (
                ('prompt', (None, '', ' ', [])),
                ('required', (None, [], 'text', [''], [None])),
                ('forbidden', (None, [], 'text', [' '], [1]))):
            for value in values:
                with self.subTest(field=field, value=value):
                    case = copy.deepcopy(self.case)
                    case['variants'][1][field] = value
                    self.assertIn(f'Invalid authorization variant {field}: status-only-update',
                                  validate.validate_authorization_variants(case))


class AuthorizationVariantPackageTests(unittest.TestCase):
    def test_package_validator_rejects_removed_variant(self):
        # Exercise the real package entrypoint as well as the isolated helper.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'package'
            shutil.copytree(validate.ROOT, root,
                            ignore=shutil.ignore_patterns('.git', '__pycache__', '.local'))
            path = root / 'evals/cases.json'
            original = path.read_text(encoding='utf-8')
            for name in ('authorization-revoked', 'status-only-update'):
                with self.subTest(name=name):
                    catalog = json.loads(original)
                    case = next(c for c in catalog['cases'] if c['id'] == 'host-authorization-revision')
                    case['variants'] = [v for v in case['variants'] if v['id'] != name]
                    path.write_text(json.dumps(catalog), encoding='utf-8')
                    self.assertIn('Missing authorization variants: ' + name, validate.validate(root))


if __name__ == '__main__':
    unittest.main()
