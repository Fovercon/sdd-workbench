"""Report rendering, run index and acceptance flow (uses a redirected
SDD_REGRESSION_ARTIFACTS directory so the real archive is never touched)."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def _report(run_id='r1'):
    return {
        'run_id': run_id, 'created_utc': '2026-10-26T00:00:00+00:00', 'profile': 'standard',
        'manifest': {'suite_ref': 'HEAD', 'revision': 'deadbeef' * 5, 'dirty': False,
                     'snapshot_hash': 'a' * 64, 'pi_version': 'pi 1.3.0',
                     'provider_model': 'deepseek/deepseek-flash'},
        'l1': {'aggregate': {'n_cases': 72, 'n_correct': 60,
                             'per_skill': {'sdd-workflow-router':
                                           {'expected': 8, 'fired': 9, 'correct': 7,
                                            'recall': 0.875, 'precision': 0.7778}},
                             'confusion_pairs': {'sdd-plan-slices <- sdd-implement-slice': 2},
                             'negatives': {'n': 8, 'false_positives': 1,
                                           'cases': [{'case': 'neg-x', 'fired': ['sdd-retrospective']}]},
                             'negative_precision': 0.875, 'enum_discipline': 0.9,
                             'router_recall': 0.875}},
        'l2': {'aggregate': {
            'conditions': {'baseline': {'n_runs': 18, 'mean_partial': 0.4, 'pass_at_k': False,
                                        'pass_cap_k': False, 'full_pass_runs': 5,
                                        'tokens_mean': 50000.0, 'seconds_mean': 300.0,
                                        'invocation_rate': 0.0},
                           'full': {'n_runs': 18, 'mean_partial': 0.6, 'pass_at_k': True,
                                    'pass_cap_k': False, 'full_pass_runs': 10,
                                    'tokens_mean': 120000.0, 'seconds_mean': 420.0,
                                    'invocation_rate': 0.95}},
            'full_vs_baseline': {'macro_delta': 0.2,
                                 'normalized_gain_per_task': {'a': 0.3, 'b': -0.1},
                                 'delta_per_task': {'a': 0.2, 'b': -0.05},
                                 'gain_nonneg_task_fraction': 0.5,
                                 'worst_task_delta': -0.05,
                                 'token_ratio': 2.4}}},
        'l3': {'aggregate': {'n_slots': 36, 'fabricated_claims': 1,
                             'fabricated_slots': [{'task': 'a', 'condition': 'full', 'trial': 't2'}],
                             'traceability_mean': 0.85, 'max_gap': 0.6,
                             'reward_hack_slots': [{'task': 'b', 'condition': 'full',
                                                    'trial': 't1', 'gap': 0.6}],
                             'ambiguity_total': 3, 'outcome_discipline': 0.8,
                             'artifact_presence': {'spec': 16, 'plan': 14, 'n_skill_slots': 18}}},
        'gates': [], 'comparison': None,
    }


class TestRenderAndIndex(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        os.environ['SDD_REGRESSION_ARTIFACTS'] = self.tmp.name
        self.addCleanup(os.environ.pop, 'SDD_REGRESSION_ARTIFACTS', None)

    def test_markdown_sections(self):
        import importlib
        import runner.paths
        importlib.reload(runner.paths)
        from runner import reporting
        importlib.reload(reporting)
        report = _report()
        report['gates'] = [
            {'id': 'l1_router_recall', 'layer': 'l1', 'metric': 'router_recall', 'op': '>=',
             'threshold': 0.8, 'observed': 0.875, 'missing': False, 'passed': True},
            {'id': 'l3_fabricated_claims', 'layer': 'l3', 'metric': 'fabricated_claims',
             'op': '<=', 'threshold': 0, 'observed': 1, 'missing': False, 'passed': False}]
        text = reporting.render_markdown(report)
        for needed in ('验收门', 'L1 触发/路由', 'L2 端到端', 'L3 过程质量', '优化方向',
                       'sdd-workflow-router', 'full−baseline 宏观差', '❌', '✅'):
            self.assertIn(needed, text)
        self.assertIn('单次运行是试点', text)

    def test_hints_cite_data(self):
        import importlib
        import runner.paths
        importlib.reload(runner.paths)
        from runner import reporting
        importlib.reload(reporting)
        hints = reporting.optimization_hints(_report())
        joined = '\n'.join(hints)
        self.assertIn('L1 相邻混淆', joined)
        self.assertIn('负例误触发', joined)
        self.assertIn('b', joined.split('L3')[0])  # negative task surfaced
        self.assertIn('编造', joined)

    def test_index_accept_and_finalize(self):
        import importlib
        import runner.paths
        importlib.reload(runner.paths)
        from runner import reporting
        importlib.reload(reporting)
        run_dir = runner.paths.runs_root() / 'r1'
        run_dir.mkdir(parents=True)
        report = _report()
        path = reporting.finalize(report, run_dir)
        self.assertTrue(Path(path).exists())
        with self.assertRaises(ValueError):
            reporting.accept('missing-run')
        reporting.accept('r1')
        index = reporting.load_index()
        self.assertEqual(index['accepted_run_id'], 'r1')
        accepted = reporting.load_accepted_report(exclude_run_id='other')
        self.assertEqual(accepted['run_id'], 'r1')
        self.assertIsNone(reporting.load_accepted_report(exclude_run_id='r1'))


if __name__ == '__main__':
    unittest.main()
