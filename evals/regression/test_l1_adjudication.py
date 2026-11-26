"""Scoring contracts: optional neighbours and operation-specific outcomes."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runner import l1_trigger


class TestScore(unittest.TestCase):
    def case(self, **extra):
        return {'expect': {'trigger': ['sdd-workflow-router']},
                'may_also': ['sdd-project-bootstrap'], **extra}

    def test_allowed_neighbour_is_correct_but_not_strict(self):
        result = l1_trigger.score(self.case(),
                                  ['sdd-workflow-router', 'sdd-project-bootstrap'],
                                  'RECONCILIATION_REQUIRED')
        self.assertTrue(result['correct'])
        self.assertFalse(result['strict_correct'])
        self.assertEqual(result['false_fires'], [])

    def test_forbidden_neighbour_or_missing_primary_fails(self):
        for fired in (['sdd-workflow-router', 'sdd-implement-slice'],
                      ['sdd-project-bootstrap']):
            self.assertFalse(l1_trigger.score(self.case(), fired, '')['correct'])

    def test_view_has_no_diagnostic_enum_requirement(self):
        case = self.case(enum_required=False)
        result = l1_trigger.score(case, ['sdd-workflow-router'], '看板已保存。')
        self.assertTrue(result['correct'])
        self.assertIsNone(result['enum_ok'])

    def test_enum_tokens_use_word_boundaries(self):
        result = l1_trigger.score(self.case(), ['sdd-workflow-router'],
                                  'NOT_NEXT_STEP_READY_YET')
        self.assertFalse(result['enum_ok'])

    def test_optional_reads_do_not_reduce_required_skill_precision(self):
        result = l1_trigger.score(self.case(),
                                  ['sdd-workflow-router', 'sdd-project-bootstrap'],
                                  'RECONCILIATION_REQUIRED')
        aggregate = l1_trigger.aggregate([result])
        self.assertEqual(aggregate['n_strict_correct'], 0)
        self.assertEqual(aggregate['per_skill']['sdd-workflow-router']['precision'], 1)
        self.assertNotIn('sdd-project-bootstrap', aggregate['per_skill'])

    def test_optional_skill_on_no_required_route_is_not_false_positive(self):
        case = {'expect': {'trigger': []}, 'may_also': ['sdd-implement-slice']}
        result = l1_trigger.score(case, ['sdd-implement-slice'], '')
        self.assertTrue(result['correct'])
        self.assertFalse(result['negative_false_positive'])

    def test_report_calls_reads_reads_not_execution(self):
        from runner import reporting
        result = l1_trigger.score(self.case(), ['sdd-workflow-router'], 'NEXT_STEP_READY')
        report = {'run_id': 'test', 'l1': {'aggregate': l1_trigger.aggregate([result])}}
        text = reporting.render_markdown(report)
        self.assertIn('成功读取', text)
        self.assertIn('不证明', text)

    def test_failed_actor_cannot_pass_a_negative_case(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)
            (dest / 'runtime').mkdir()
            (dest / 'events.jsonl').write_text('')
            (dest / 'process-result.json').write_text(json.dumps({'exit_code': 1}))
            case = {'id': 'failed', 'category': 'negative', 'expect': {'trigger': []}}
            result = l1_trigger.adjudicate(case, dest, dest / 'runtime')
            aggregate = l1_trigger.aggregate([result])
            self.assertEqual(aggregate['n_invalid'], 1)
            self.assertEqual(aggregate['n_correct'], 0)
            self.assertIsNone(aggregate['negative_precision'])

    def test_hints_do_not_prescribe_skill_changes_from_reads_alone(self):
        from runner import reporting
        report = {'l1': {'aggregate': {
            'per_skill': {'sdd-workflow-router': {'recall': 0.5}},
            'confusion_pairs': {'sdd-code-review <- sdd-converge-review': 1}}}}
        hints = '\n'.join(reporting.optimization_hints(report))
        self.assertNotIn('优先改 SKILL.md', hints)
        self.assertNotIn('互写排除条件', hints)
        self.assertIn('原始', hints)


if __name__ == '__main__':
    unittest.main()
