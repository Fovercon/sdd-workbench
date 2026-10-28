import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from evaluate_workflow import evaluate

ROOT = Path(__file__).resolve().parents[2]
CASES = ('intake-late', 'intake-early')


class IntakeProtocolTests(unittest.TestCase):
    def prepare(self, case, output, ref=None):
        command = [sys.executable, '-B', str(ROOT/'evals/context/prepare_workflow.py'),
                   '--case', case, '--output', str(output)]
        if ref:
            command += ['--ref', ref]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_public_cli_freezes_ref_and_inputs_and_rejects_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            for case in CASES:
                with self.subTest(case=case):
                    a, b = Path(directory)/(case+'-ref'), Path(directory)/(case+'-current')
                    self.prepare(case, a, 'HEAD'); self.prepare(case, b)
                    x, y = [json.loads((t/'input-receipt.json').read_text()) for t in (a,b)]
                    self.assertEqual(x['project'], y['project'])
                    self.assertEqual((a/'prompt.txt').read_bytes(), (b/'prompt.txt').read_bytes())
                    for trial, receipt in ((a,x),(b,y)):
                        self.assertTrue((trial/'runtime/sdd-implement-slice/SKILL.md').is_file())
                        for name, digest in receipt['runtime'].items():
                            self.assertEqual(hashlib.sha256((trial/'runtime'/name).read_bytes()).hexdigest(), digest)
                    result = subprocess.run([sys.executable, '-B', str(ROOT/'evals/context/prepare_workflow.py'),
                                             '--case', case, '--output', str(a)], capture_output=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(json.loads((a/'input-receipt.json').read_text()), x)

    def test_two_states_have_opposite_name_rejection_timing(self):
        with tempfile.TemporaryDirectory() as directory:
            for case in CASES:
                trial = Path(directory)/case; self.prepare(case, trial)
                script = """from pathlib import Path
import tempfile
from intake import intake, RejectedRecord
with tempfile.TemporaryDirectory() as d:
 root=Path(d)/'result'
 try: intake([{'name':'ok.txt','kind':'file','data':b'ok'},
              {'name':'blocked.txt','kind':'file','data':b'bad'}],root)
 except RejectedRecord: pass
 print((root/'ok.txt').exists(), (root/'blocked.txt').exists())
"""
                result = subprocess.run([sys.executable,'-B','-c',script],cwd=trial/'project',capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(result.stdout.strip(),'True False' if case=='intake-late' else 'False False')

    def test_guard_distinguishes_real_fix_from_green_inherited_suite(self):
        with tempfile.TemporaryDirectory() as directory:
            for case in CASES:
                trial = Path(directory)/case; self.prepare(case,trial)
                self.assertEqual(evaluate(case,trial)['automated_guards'],'FAIL')
                (trial/'project/IMPLEMENTATION.md').write_text('Mechanical output only, not semantic acceptance.\n')
                self.assertEqual(evaluate(case,trial)['automated_guards'],'FAIL')
                code=trial/'project/intake.py'
                original=code.read_text()
                code.write_text(original.replace('record["kind"] in {"link", "fifo"}',
                                                 'record["kind"] not in {"file", "dir"}'))
                self.assertEqual(evaluate(case,trial)['automated_guards'],'PASS')
                protected=trial/'project/SPEC.md'; data=protected.read_bytes()
                protected.write_bytes(data+b'\nchanged\n')
                self.assertEqual(evaluate(case,trial)['automated_guards'],'FAIL')
                protected.write_bytes(data)
                self.assertFalse(evaluate('direct',trial)['case_identity_matches'])
                self.assertEqual(evaluate(case,trial)['automated_guards'],'PASS')


if __name__ == '__main__':
    unittest.main()
