import json
from pathlib import Path
import tempfile
import unittest

from evaluate_workflow import evaluate
from prepare_workflow import prepare


class WorkflowIdentityTests(unittest.TestCase):
    def planning_run(self, base):
        run = prepare('plan-local', Path(base) / 'run')
        design = run / 'project/design'
        design.mkdir()
        for name in ('plan.md', 'tasks.md'):
            (design / name).write_text('Synthetic output; manual semantic review required.\n')
        return run

    def test_wrong_readonly_case_cannot_certify_planning(self):
        with tempfile.TemporaryDirectory() as base:
            run = prepare('plan-local', Path(base) / 'run')
            result = evaluate('risk', run)
            self.assertEqual(result['automated_guards'], 'FAIL')
            self.assertFalse(result['case_identity_matches'])
            self.assertEqual(result['case'], 'risk')
            self.assertEqual(result['frozen_case'], 'plan-local')

    def test_wrong_implementation_case_does_not_execute_project_code(self):
        with tempfile.TemporaryDirectory() as base:
            run = self.planning_run(base)
            marker = run / 'project/probe-ran.txt'
            (run / 'project/service.py').write_text(
                'from pathlib import Path\n'
                f'Path({str(marker)!r}).write_text("executed")\n'
                'def select(items, key):\n'
                '    return [item for item in items if item["id"] == key]\n')
            result = evaluate('direct', run)
            self.assertFalse(marker.exists(), 'mismatched case executed project code')
            self.assertFalse((run / 'controller-tests.stdout').exists())
            self.assertEqual(result['automated_guards'], 'FAIL')
            self.assertFalse(result['case_identity_matches'])

    def test_matching_case_is_recorded_and_missing_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as base:
            run = self.planning_run(base)
            result = evaluate('plan-local', run)
            self.assertEqual(result['automated_guards'], 'PASS')
            self.assertTrue(result['case_identity_matches'])
            self.assertEqual(result['case'], 'plan-local')
            variant_path = run / 'variant.json'
            original = json.loads(variant_path.read_text())
            for bad in ({'source': original['source']}, [], {'case': None}):
                with self.subTest(variant=bad):
                    variant_path.write_text(json.dumps(bad))
                    self.assertEqual(evaluate('plan-local', run)['automated_guards'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
