"""Protocol self-tests: harness stays outside package inputs; configs stay valid;
the Pi argv stays byte-compatible with evals/context/run_pi.py."""
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from runner import pi_runner  # noqa: E402
from runner.paths import CONFIG, ROOT as RUNNER_ROOT  # noqa: E402


def _load_package_module():
    spec = importlib.util.spec_from_file_location('sdd_package', ROOT / 'tools' / 'package.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestNotAPackageInput(unittest.TestCase):
    def test_no_regression_paths_in_bundle(self):
        package = _load_package_module()
        files = [str(p) for p in package.bundle_files(ROOT)]
        leaked = [p for p in files if p.startswith('evals/regression')]
        self.assertEqual(leaked, [], 'regression harness must stay outside package inputs')

    def test_no_harness_paths_in_bundle_even_nested(self):
        package = _load_package_module()
        files = [str(p) for p in package.bundle_files(ROOT)]
        leaked = [p for p in files if '/evals/regression/' in p]
        self.assertEqual(leaked, [])


class TestConfigs(unittest.TestCase):
    def test_conditions_schema(self):
        data = json.loads((CONFIG / 'conditions.json').read_text(encoding='utf-8'))
        self.assertIn('conditions', data)
        ids = [c['id'] for c in data['conditions']]
        self.assertEqual(ids, ['baseline', 'full', 'core5', 'no-router', 'directed'])
        for cond in data['conditions']:
            self.assertIsInstance(cond['skills'], list)
            self.assertIn(cond.get('prompt', 'organic'), ('organic', 'directed'))
        full = next(c for c in data['conditions'] if c['id'] == 'full')
        self.assertEqual(full['skills'], ['ALL'])
        directed = next(c for c in data['conditions'] if c['id'] == 'directed')
        self.assertEqual(directed['skills'], ['ALL'])
        self.assertEqual(directed['prompt'], 'directed')

    def test_gates_schema(self):
        data = json.loads((CONFIG / 'gates.json').read_text(encoding='utf-8'))
        ids = [g['id'] for g in data['gates']]
        self.assertEqual(len(ids), len(set(ids)))
        for gate in data['gates']:
            self.assertIn(gate['op'], ('>=', '<='))
            self.assertIsInstance(gate['value'], (int, float))
            self.assertIn(gate['layer'], ('l1', 'l2', 'l3'))


class TestCanonicalArgv(unittest.TestCase):
    def _run_pi_flags(self):
        source = (ROOT / 'evals' / 'context' / 'run_pi.py').read_text(encoding='utf-8')
        argv_line = next(line for line in source.splitlines() if line.lstrip().startswith('argv='))
        return re.findall(r"'(--[a-z-]+)'", argv_line)

    def _built_flags(self, **kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / 'project').mkdir()
            (base / 'prompt.txt').write_text('p', encoding='utf-8')
            argv = pi_runner.build_argv(base, '/usr/bin/pi', **kwargs)
        return [a for a in argv if a.startswith('--')]

    def test_flag_order_matches_run_pi_when_skills_given(self):
        runtime = Path('/tmp/whatever-runtime')
        self.assertEqual(self._built_flags(skills_dir=runtime), self._run_pi_flags())

    def test_baseline_omits_skill_flag(self):
        flags = self._built_flags()
        self.assertNotIn('--skill', flags)
        self.assertEqual(flags, [f for f in self._run_pi_flags() if f != '--skill'])

    def test_provider_model_explicit(self):
        self.assertEqual(pi_runner.PROVIDER, 'deepseek')
        self.assertEqual(pi_runner.MODEL, 'deepseek-flash')


if __name__ == '__main__':
    unittest.main()
