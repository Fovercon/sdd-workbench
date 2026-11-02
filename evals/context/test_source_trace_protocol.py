from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest

from evaluate_workflow import evaluate

ROOT = Path(__file__).resolve().parents[2]
CASES = ('trace-source-current', 'trace-source-stale')


class SourceTraceProtocolTests(unittest.TestCase):
    def prepare(self, case, output, ref=None):
        command = [sys.executable, '-B', str(ROOT / 'evals/context/prepare_workflow.py'),
                   '--case', case, '--output', str(output)]
        if ref:
            command += ['--ref', ref]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_public_ref_preserves_paired_project_and_prompt_and_freezes_original_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            for case in CASES:
                a, b = [Path(directory) / (case + suffix) for suffix in ('-old', '-new')]
                self.prepare(case, a, 'HEAD'); self.prepare(case, b)
                x, y = [json.loads((p / 'input-receipt.json').read_text()) for p in (a, b)]
                self.assertEqual(x['project'], y['project'])
                self.assertEqual((a / 'prompt.txt').read_bytes(), (b / 'prompt.txt').read_bytes())
                observations = json.loads((b / 'project/observations.json').read_text(encoding='utf-8'))
                ref = next(i for i in observations['items'] if i['id'] == 'R-RULE')['sources'][0]
                actual = hashlib.sha256((b / 'project/RULE.md').read_bytes()).hexdigest()
                self.assertEqual(ref['sha256'] == actual, case == 'trace-source-current')
                for name, digest in y['runtime'].items():
                    self.assertEqual(hashlib.sha256((b / 'runtime' / name).read_bytes()).hexdigest(), digest)

    def test_real_query_distinguishes_historical_pass_from_source_freshness_and_unmapped_path(self):
        with tempfile.TemporaryDirectory() as directory:
            for case in CASES:
                trial = Path(directory) / case; self.prepare(case, trial)
                command = [sys.executable, str(trial / 'runtime/sdd-workflow-router/scripts/project_view.py'),
                           'trace', '--root', str(trial / 'project'), '--input', str(trial / 'project/observations.json'),
                           '--changed-source', 'RULE.md', '--changed-source', 'unmapped.md']
                result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(result.returncode, 0 if case.endswith('current') else 2, result.stderr)
                report = json.loads(result.stdout); rows = {r['id']: r for r in report['items']}
                self.assertEqual(report['changed_ids'], ['R-RULE'])
                self.assertEqual(report['unmapped_sources'], ['unmapped.md'])
                self.assertEqual(rows['T-WORK']['selection'], 'REACHED')
                self.assertEqual(rows['T-WORK']['recorded_result'], 'PASS')
                self.assertEqual(rows['T-WORK']['freshness'], 'CURRENT' if case.endswith('current') else 'STALE')
                self.assertEqual(rows['T-OTHER']['selection'], 'NO_RECORDED_PATH')
                self.assertEqual(rows['T-OTHER']['freshness'], 'CURRENT')
                self.assertFalse(list((trial / 'runtime').rglob('*.pyc')))

    def test_guard_requires_report_and_preserves_all_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            for case in CASES:
                trial = Path(directory) / case; self.prepare(case, trial)
                self.assertEqual(evaluate(case, trial)['automated_guards'], 'FAIL')
                (trial / 'project/TRACE.md').write_text('Placeholder is not semantic acceptance.\n')
                self.assertEqual(evaluate(case, trial)['automated_guards'], 'PASS')
                original = (trial / 'project/RULE.md').read_bytes()
                (trial / 'project/RULE.md').write_bytes(original + b'changed\n')
                self.assertEqual(evaluate(case, trial)['automated_guards'], 'FAIL')
                (trial / 'project/RULE.md').write_bytes(original)
                self.assertFalse(evaluate('impact-proposed', trial)['case_identity_matches'])


if __name__ == '__main__':
    unittest.main()
