"""Statistics and gate-evaluation self-tests."""
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from runner import compare, l2_e2e  # noqa: E402


class TestNormalizedGain(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(l2_e2e.normalized_gain(0.5, 0.75), 0.5)

    def test_saturated_base_is_none(self):
        self.assertIsNone(l2_e2e.normalized_gain(1.0, 1.0))

    def test_none_inputs(self):
        self.assertIsNone(l2_e2e.normalized_gain(None, 0.5))

    def test_negative_gain(self):
        self.assertEqual(l2_e2e.normalized_gain(0.5, 0.25), -0.5)


class TestBootstrap(unittest.TestCase):
    def test_deterministic(self):
        values = [0.1, 0.4, 0.6, 0.9, 1.0]
        first = l2_e2e.bootstrap_ci(values)
        second = l2_e2e.bootstrap_ci(values)
        self.assertEqual(first, second)

    def test_bounds_contain_mean(self):
        ci = l2_e2e.bootstrap_ci([0.0, 0.5, 1.0, 0.2])
        self.assertLessEqual(ci['p5'], ci['mean'])
        self.assertGreaterEqual(ci['p95'], ci['mean'])

    def test_empty(self):
        self.assertIsNone(l2_e2e.bootstrap_ci([]))


class TestAggregate(unittest.TestCase):
    @staticmethod
    def slot(task, cond, trial, hidden_partial, visible=None, tokens=1000, fired=None):
        return {'task': task, 'condition': cond, 'trial': f't{trial}',
                'hidden': {'total': 10, 'passed': int(hidden_partial * 10)},
                'hidden_partial': hidden_partial,
                'visible': None, 'visible_partial': visible,
                'gap': (visible - hidden_partial) if visible is not None else None,
                'fired_skills': fired or [], 'usage': {'input': tokens, 'cache_read': 0,
                                                       'cache_write': 0, 'output': 0},
                'seconds': 100.0, 'exit_code': 0}

    def test_aggregate_two_conditions(self):
        results = []
        for task in ('a', 'b'):
            results.append(self.slot(task, 'baseline', 1, 0.4, tokens=800))
            results.append(self.slot(task, 'full', 1, 0.8, tokens=1000, fired=['sdd-plan-slices']))
        metrics = l2_e2e.aggregate(results, [{'id': 'baseline'}, {'id': 'full'}])
        self.assertEqual(metrics['conditions']['full']['mean_partial'], 0.8)
        self.assertEqual(metrics['conditions']['baseline']['mean_partial'], 0.4)
        self.assertEqual(metrics['conditions']['full']['input_mean'], 1000.0)
        fvb = metrics['full_vs_baseline']
        self.assertEqual(fvb['macro_delta'], 0.4)
        self.assertEqual(fvb['normalized_gain_per_task'], {'a': round((0.8 - 0.4) / 0.6, 4),
                                                           'b': round((0.8 - 0.4) / 0.6, 4)})
        self.assertEqual(fvb['worst_task_delta'], 0.4)
        self.assertEqual(fvb['input_overhead'], 200.0)
        self.assertEqual(fvb['input_ratio'], 1.25)
        self.assertEqual(metrics['conditions']['full']['invocation_rate'], 1.0)

    def test_pass_cap_requires_all_trials(self):
        results = [self.slot('a', 'full', 1, 1.0), self.slot('a', 'full', 2, 1.0),
                   self.slot('a', 'full', 3, 0.5)]
        metrics = l2_e2e.aggregate(results, [{'id': 'full'}])
        self.assertTrue(metrics['conditions']['full']['pass_at_k'])
        self.assertFalse(metrics['conditions']['full']['pass_cap_k'])

    def test_cache_write_is_part_of_total_tokens(self):
        slot = self.slot('a', 'full', 1, 1.0, tokens=11)
        slot['usage'].update({'cache_read':3,'cache_write':2,'output':7,'complete':True})
        metrics = l2_e2e.aggregate([slot], [{'id':'full'}])
        self.assertEqual(metrics['conditions']['full']['tokens_total'], 23)

    def test_unavailable_usage_does_not_pass_cost_gate_as_zero(self):
        rows = [self.slot('a', cond, 1, 1.0, tokens=1000)
                for cond in ('baseline','full','directed')]
        rows[1]['usage']['complete'] = False
        rows[2]['usage']['complete'] = False
        metrics = l2_e2e.aggregate(rows, [{'id':c} for c in ('baseline','full','directed')])
        for cond in ('full','directed'):
            self.assertIsNone(metrics['conditions'][cond]['tokens_total'])
            self.assertIsNone(metrics['conditions'][cond]['tokens_mean'])
        self.assertIsNone(metrics['full_vs_baseline']['token_ratio'])
        self.assertIsNone(metrics['directed_vs_baseline']['token_ratio'])


class TestGates(unittest.TestCase):
    def test_pass_fail_and_missing(self):
        metrics = {'l1': {'router_recall': 0.9, 'negative_precision': 1.0, 'enum_discipline': 0.95},
                   'l2': {'full_minus_baseline_macro': 0.1, 'gain_nonneg_task_fraction': 1.0,
                          'worst_task_delta': -0.1, 'full_over_baseline_token_ratio': 2.0,
                          'directed_invocation': 1.0, 'directed_minus_baseline_macro': 0.05,
                          'directed_over_baseline_token_ratio': 4.0},
                   'l3': {'fabricated_claims': 0, 'traceability_mean': 0.85, 'max_gap': 0.2}}
        gates = compare.evaluate_gates(metrics)
        by_id = {g['id']: g for g in gates}
        self.assertTrue(all(g['passed'] for g in gates), [g for g in gates if not g['passed']])
        self.assertEqual(by_id['l1_router_recall']['observed'], 0.9)

        metrics['l3']['fabricated_claims'] = 2
        metrics['l2']['directed_invocation'] = 0.5
        gates = compare.evaluate_gates(metrics)
        self.assertFalse(next(g for g in gates if g['id'] == 'l3_fabricated_claims')['passed'])
        self.assertFalse(next(g for g in gates if g['id'] == 'l2_directed_invocation')['passed'])

        gates = compare.evaluate_gates({'l1': {'router_recall': 0.9}})
        for gate in gates:
            if gate['layer'] != 'l1':
                self.assertTrue(gate['missing'])
                self.assertFalse(gate['passed'])

    def test_configured_gates_load(self):
        gates = compare.load_gates()
        self.assertGreaterEqual(len(gates), 13)


class TestProcessScore(unittest.TestCase):
    TASK = {'process': {
        'reply_must_match': ['NOT_CONVERGED|HUMAN_DECISION_REQUIRED'],
        'reply_must_not_match': ['Decision:\\s*CONVERGED'],
        'min_question_marks': 2,
        'artifact': 'design/reports/convergence.md',
        'artifact_must_match': ['NOT_CONVERGED'],
        'artifact_must_not_match': ['Decision:\\s*CONVERGED'],
        'weights': {'reply': 0.5, 'artifact': 0.5},
    }}

    def test_full_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            art = Path(tmp) / 'design/reports/convergence.md'
            art.parent.mkdir(parents=True)
            art.write_text('Decision: NOT_CONVERGED\nFR-003 MISSING\n', encoding='utf-8')
            score, comps = l2_e2e.process_score(self.TASK, tmp,
                                                'NOT_CONVERGED,请确认以下问题??')
            self.assertEqual(score, 1.0)
            self.assertEqual(comps['reply'], 1.0)
            self.assertEqual(comps['artifact'], 1.0)

    def test_empty_reply_and_missing_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            score, comps = l2_e2e.process_score(self.TASK, tmp, '')
            self.assertLess(score, 1.0)
            self.assertEqual(comps['reply'], 0.0)
            self.assertEqual(comps['artifact'], 0.0)

    def test_must_not_zeroes_reply(self):
        with tempfile.TemporaryDirectory() as tmp:
            score, comps = l2_e2e.process_score(
                self.TASK, tmp, 'Decision: CONVERGED 全部通过 NOT_CONVERGED')
            self.assertEqual(comps['reply'], 0.0)

    def test_hidden_component(self):
        task = {'process': {'reply_must_match': ['IMPACT_READY'],
                            'weights': {'reply': 0.4, 'hidden': 0.6}}}
        with tempfile.TemporaryDirectory() as tmp:
            score, comps = l2_e2e.process_score(task, tmp, 'IMPACT_READY', hidden_partial=0.5)
            self.assertEqual(comps['hidden'], 0.5)
            self.assertEqual(score, round((1.0 * 0.4 + 0.5 * 0.6), 4))


if __name__ == '__main__':
    unittest.main()
