"""Task assets, not model or human usability certification."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
PILOT=ROOT/'skills/sdd-workflow-router/evals/forward/prepare_pilot.py'
LAYOUT=ROOT/'skills/sdd-plan-slices/evals/forward/prepare_layout.py'


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


pilot=module('pilot_inputs',PILOT);layout=module('layout_inputs',LAYOUT)
probe=module('pilot_probe',PILOT.parents[1]/'assert_pilot.py')


class PilotInputs(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.base=Path(self.temp.name)

    def test_five_tasks_prepare_without_external_assets_or_answers(self):
        for case in pilot.CASES:
            with self.subTest(case=case):
                a=pilot.prepare(self.base/(case+'-a'),case);b=pilot.prepare(self.base/(case+'-b'),case)
                self.assertEqual(a,b)
                self.assertIn('REQUEST.md',a);self.assertIn('notes.txt',a)
                self.assertFalse(any('receipt' in name or 'probe' in name for name in a))

    def test_default_and_custom_layout_inputs_keep_identical_product_obligations(self):
        a=layout.prepare(self.base/'default');b=layout.prepare(self.base/'custom','custom')
        self.assertEqual({k:v for k,v in a.items() if k!='AGENTS.md'},{k:v for k,v in b.items() if k!='AGENTS.md'})
        self.assertTrue((self.base/'custom/AGENTS.md').read_text().startswith((self.base/'default/AGENTS.md').read_text()))
        with self.assertRaises(ValueError):layout.prepare(self.base/'default')

    def test_change_seed_is_green_but_resume_seed_fails_existing_behavior(self):
        for case,expected in [('change',0),('resume',1)]:
            project=self.base/case;pilot.prepare(project,case)
            result=subprocess.run([sys.executable,'-B','-m','unittest','discover'],cwd=project,capture_output=True,text=True)
            self.assertEqual(result.returncode,expected,result.stderr)
        historical=json.loads((self.base/'resume/evidence/old-verification.json').read_text())
        import hashlib
        self.assertNotEqual(historical['source']['jobs.py'],hashlib.sha256((self.base/'resume/jobs.py').read_bytes()).hexdigest())
        self.assertEqual((self.base/'change/design/spec.md').read_bytes(),(self.base/'resume/design/spec.md').read_bytes())

    def test_cli_keeps_receipt_outside_inputs(self):
        target=self.base/'project';receipt=self.base/'receipt.json'
        result=subprocess.run([sys.executable,'-B',str(PILOT),'--case','resume','--output',str(target),'--receipt',str(receipt)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(receipt.read_text())['inputs'],pilot.hashes(target))
        invalid=self.base/'invalid'
        result=subprocess.run([sys.executable,'-B',str(PILOT),'--case','review','--output',str(invalid),'--receipt',str(invalid/'receipt.json')],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0);self.assertFalse(invalid.exists())

    def test_probe_rejects_original_bugs_and_protected_file_edits(self):
        for case in ('bug','feature','change','resume'):
            project=self.base/case;inputs=pilot.prepare(project,case)
            with self.subTest(case=case),self.assertRaises(AssertionError):
                probe.evaluate(project,{'inputs':inputs},case)
            if case in ('change','resume'):
                corrected=pilot.JOB
                if case=='change':corrected=corrected.replace("r['state']=='failed'","r['state'] in ('failed','cancelled')")
                (project/'jobs.py').write_text(corrected)
                # A green known-state suite still misses wrong-exception rejection.
                with self.assertRaisesRegex(AssertionError,'Wrong rejection exception'):
                    probe.evaluate(project,{'inputs':inputs},case)
                corrected=corrected.replace("r['state'] not in STATES","r['state'] not in tuple(STATES)")
                (project/'jobs.py').write_text(corrected)
                self.assertEqual(probe.evaluate(project,{'inputs':inputs},case)['result'],'PASS')
                (project/'notes.txt').write_text('lost user edits')
                with self.assertRaises(AssertionError):probe.evaluate(project,{'inputs':inputs},case)
        project=self.base/'review';inputs=pilot.prepare(project,'review')
        self.assertEqual(probe.evaluate(project,{'inputs':inputs},'review')['result'],'PASS')
        (project/'retry.py').write_text('unauthorized repair')
        with self.assertRaises(AssertionError):probe.evaluate(project,{'inputs':inputs},'review')


if __name__=='__main__':unittest.main()
