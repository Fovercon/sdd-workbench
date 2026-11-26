import os
import tempfile
import unittest

from config import ConfigError, coerce, merge

DEFAULTS = {'db': {'host': 'localhost', 'port': 5432, 'retries': 3},
            'features': {'cache': True, 'beta': ['a', 'b']},
            'name': 'svc'}


class TestCoerce(unittest.TestCase):
    def test_bool_case_insensitive(self):
        self.assertIs(coerce('TRUE'), True)
        self.assertIs(coerce('false'), False)

    def test_int_and_float(self):
        self.assertEqual(coerce('42'), 42)
        self.assertEqual(coerce('-7'), -7)
        self.assertEqual(coerce('3.14'), 3.14)

    def test_string_passthrough(self):
        self.assertEqual(coerce('hello'), 'hello')
        self.assertEqual(coerce('1.2.3'), '1.2.3')


class TestMerge(unittest.TestCase):
    def test_defaults_only(self):
        self.assertEqual(merge(DEFAULTS), DEFAULTS)

    def test_input_not_mutated(self):
        snapshot = {'db': {'host': 'localhost'}}
        merge(snapshot, env={'APP_DB__HOST': 'db-1'})
        self.assertEqual(snapshot, {'db': {'host': 'localhost'}})

    def test_file_overrides_nested(self):
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as fh:
            fh.write('{"db": {"host": "file-host"}, "name": "file-svc"}')
            path = fh.name
        self.addCleanup(os.unlink, path)
        merged = merge(DEFAULTS, file_path=path)
        self.assertEqual(merged['db']['host'], 'file-host')
        self.assertEqual(merged['db']['port'], 5432)
        self.assertEqual(merged['name'], 'file-svc')

    def test_env_beats_file(self):
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as fh:
            fh.write('{"db": {"host": "file-host"}}')
            path = fh.name
        self.addCleanup(os.unlink, path)
        merged = merge(DEFAULTS, file_path=path, env={'APP_DB__HOST': 'env-host'})
        self.assertEqual(merged['db']['host'], 'env-host')

    def test_env_coercion_and_unknown_path_ignored(self):
        merged = merge(DEFAULTS, env={'APP_DB__PORT': '6543',
                                      'APP_DB__TIMEOUT': '9',
                                      'APP_UNKNOWN__X': '1',
                                      'NOT_APP': 'nope'})
        self.assertEqual(merged['db']['port'], 6543)
        self.assertNotIn('timeout', merged['db'])
        self.assertNotIn('unknown', merged)
        self.assertNotIn('NOT_APP', merged)

    def test_list_replaced_not_merged(self):
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as fh:
            fh.write('{"features": {"beta": ["z"]}}')
            path = fh.name
        self.addCleanup(os.unlink, path)
        merged = merge(DEFAULTS, file_path=path)
        self.assertEqual(merged['features']['beta'], ['z'])

    def test_missing_file_ignored(self):
        merged = merge(DEFAULTS, file_path='no-such-9371.json', env={})
        self.assertEqual(merged['db']['host'], 'localhost')

    def test_invalid_json_raises(self):
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as fh:
            fh.write('{not json')
            path = fh.name
        self.addCleanup(os.unlink, path)
        with self.assertRaises(ConfigError):
            merge(DEFAULTS, file_path=path)

    def test_json_array_raises(self):
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as fh:
            fh.write('[1,2]')
            path = fh.name
        self.addCleanup(os.unlink, path)
        with self.assertRaises(ConfigError):
            merge(DEFAULTS, file_path=path)
