"""Task-pack integrity: oracle passes hidden tests 100%, the bare starter does
not, and nothing evaluator-owned leaks into the actor-visible project tree."""
import json
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from runner import l2_e2e  # noqa: E402


def _run(tests_dir, project_dir):
    env = dict(os.environ, PYTHONPATH=str(project_dir))
    proc = subprocess.run([sys.executable, '-B',
                           str(HERE / 'runner' / '_run_tests.py'), str(tests_dir)],
                          cwd=project_dir, env=env, capture_output=True, text=True, timeout=300)
    line = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else '{}'
    return json.loads(line)


class TestTaskPacks(unittest.TestCase):
    def test_change_request_public_query_examples_match_oracle(self):
        task = next(t for t in l2_e2e.load_tasks() if t['id'] == 'change-request')
        examples = {int(index):int(delay) for index, delay in
                    re.findall(r'delay_before\((\d+)\)\s*=\s*(\d+)', task['entry_prompt'])}
        self.assertEqual(examples, {6:30,9:30})
        spec = importlib.util.spec_from_file_location(
            'contract_retry', task['root'] / 'oracle/solution/retry.py')
        oracle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(oracle)
        policy = oracle.RetryPolicy()
        for index, delay in examples.items():
            self.assertEqual(policy.delay_before(index), delay)
        self.assertEqual(policy.attempts(), 6)

    def test_change_request_positive_integer_query_does_not_overflow(self):
        task = next(t for t in l2_e2e.load_tasks() if t['id'] == 'change-request')
        spec = importlib.util.spec_from_file_location(
            'large_contract_retry', task['root'] / 'oracle/solution/retry.py')
        oracle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(oracle)
        self.assertEqual(oracle.RetryPolicy().delay_before(1_000_000), 30)

    def test_packs_valid(self):
        tasks = l2_e2e.load_tasks()
        self.assertGreaterEqual(len(tasks), 9)
        for task in tasks:
            with self.subTest(task=task['id']):
                with tempfile.TemporaryDirectory() as tmp:
                    oracle_proj = Path(tmp) / 'oracle'
                    shutil.copytree(task['root'] / 'project', oracle_proj)
                    for f in (task['root'] / 'oracle' / 'solution').rglob('*'):
                        if f.is_file():
                            target = oracle_proj / f.relative_to(task['root'] / 'oracle' / 'solution')
                            target.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(f, target)
                    if task['kind'] == 'code':
                        result = _run(task['root'] / 'hidden' / 'tests', oracle_proj)
                        self.assertEqual(result.get('passed'), result.get('total'))
                        self.assertGreater(result.get('total', 0), 10,
                                           'hidden suite should have meaningful size')
                    else:
                        reply = (task['root'] / 'oracle' / 'reply.txt').read_text(encoding='utf-8')
                        hidden_partial = None
                        if (task['root'] / 'hidden' / 'tests').is_dir():
                            result = _run(task['root'] / 'hidden' / 'tests', oracle_proj)
                            self.assertEqual(result.get('passed'), result.get('total'))
                            hidden_partial = round(result['passed'] / result['total'], 4)
                        score, components = l2_e2e.process_score(task, oracle_proj, reply,
                                                                 hidden_partial)
                        self.assertEqual(score, 1.0, f'components={components}')

    def test_starter_not_passing(self):
        for task in l2_e2e.load_tasks():
            with self.subTest(task=task['id']):
                with tempfile.TemporaryDirectory() as tmp:
                    starter = Path(tmp) / 'starter'
                    shutil.copytree(task['root'] / 'project', starter)
                    if task['kind'] == 'code':
                        result = _run(task['root'] / 'hidden' / 'tests', starter)
                        self.assertLess(result.get('passed', 0), result.get('total', 0))
                    else:
                        score, _ = l2_e2e.process_score(task, starter, '')
                        self.assertLess(score, 1.0)

    def test_no_evaluator_leakage_into_project(self):
        for task in l2_e2e.load_tasks():
            with self.subTest(task=task['id']):
                project = task['root'] / 'project'
                if task['kind'] == 'code':
                    tests = list(project.rglob('test_*.py'))
                    self.assertEqual(tests, [], 'code starter project must ship no tests')
                for path in project.rglob('*'):
                    if path.is_file():
                        text = path.read_text(encoding='utf-8', errors='replace')
                        for marker in ('oracle', 'HIDDEN', 'hidden/tests'):
                            self.assertNotIn(marker, text,
                                             f'{path} leaks evaluator marker {marker}')

    def test_prompts_per_class(self):
        tasks = l2_e2e.load_tasks()
        code = [t for t in tasks if t['kind'] == 'code']
        organic = {t['entry_prompt'] for t in code}
        directed_code = {t['directed_prompt'] for t in code}
        self.assertEqual(len(organic), 1, 'organic entry prompt identical across code tasks')
        self.assertEqual(len(directed_code), 1, 'directed prompt identical across code tasks')
        for task in tasks:
            self.assertNotEqual(task['directed_prompt'], task['entry_prompt'])
            self.assertIn('必须先读 ../runtime/sdd-workflow-router/SKILL.md', task['directed_prompt'])
            self.assertNotIn('../runtime', task['entry_prompt'])
            self.assertTrue(task['directed_prompt'].endswith(task['entry_prompt']),
                            'directed prompt must only prepend the directive')

    def test_condition_resolution(self):
        conditions = l2_e2e.load_conditions()
        by_id = {c['id']: c for c in conditions}
        self.assertEqual(by_id['baseline']['skills'], [])
        from runner.paths import suite_skills
        self.assertEqual(by_id['full']['skills'], suite_skills())
        self.assertEqual(by_id['full']['prompt'], 'organic')
        self.assertEqual(by_id['directed']['skills'], suite_skills())
        self.assertEqual(by_id['directed']['prompt'], 'directed')
        self.assertNotIn('sdd-workflow-router', by_id['no-router']['skills'])


if __name__ == '__main__':
    unittest.main()
