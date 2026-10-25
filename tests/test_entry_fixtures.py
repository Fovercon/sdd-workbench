"""Entry evaluation inputs and public reference contracts; not Agent behavior tests."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
ENTRY=ROOT/'skills/sdd-workflow-router/evals/forward/prepare_entry.py'
spec=importlib.util.spec_from_file_location('prepare_entry',ENTRY)
prepare=importlib.util.module_from_spec(spec);spec.loader.exec_module(prepare)


class EntryFixtures(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)

    def test_all_cases_are_reproducible_without_evaluator_files_or_implicit_writes(self):
        for case in prepare.CASES:
            with self.subTest(case=case):
                a=prepare.prepare(self.base/(case+'-a'),case)
                b=prepare.prepare(self.base/(case+'-b'),case)
                self.assertEqual(a,b)
                self.assertTrue({'AGENTS.md','REQUEST.md','notes.txt'}.issubset(a))
                self.assertFalse(any('receipt' in name or 'probe' in name or 'trace' in name for name in a))
        self.assertFalse((self.base/'observations').exists())
        with self.assertRaises(ValueError):prepare.prepare(self.base/'bounded-a','bounded')

    def test_bounded_and_reserved_share_real_bug_and_original_green_safety_net(self):
        projects=[]
        for case in ('bounded','reserved'):
            project=self.base/case;prepare.prepare(project,case);projects.append(project)
            result=subprocess.run([sys.executable,'-B','-m','unittest','discover'],cwd=project,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            module_spec=importlib.util.spec_from_file_location('input_retry_'+case,project/'retry.py')
            value=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(value)
            self.assertEqual(value.parse_retries('-1'),-1)
            self.assertEqual(value.parse_retries('0'),0)
        for name in ('retry.py','test_retry.py','README.md','notes.txt'):
            self.assertEqual((projects[0]/name).read_bytes(),(projects[1]/name).read_bytes())
        self.assertTrue((projects[1]/'spec.md').is_file())
        self.assertTrue((projects[1]/'plan.md').is_file())
        self.assertFalse((projects[0]/'spec.md').exists())

    def test_cli_receipt_freezes_inputs_and_rejects_in_project_answers(self):
        project=self.base/'project';receipt=self.base/'receipt.json'
        result=subprocess.run([sys.executable,'-B',str(ENTRY),'--case','bounded','--output',str(project),'--receipt',str(receipt)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        value=json.loads(receipt.read_text(encoding='utf-8'))
        for name,sha in value['inputs'].items():self.assertEqual(hashlib.sha256((project/name).read_bytes()).hexdigest(),sha)
        invalid=self.base/'invalid'
        result=subprocess.run([sys.executable,'-B',str(ENTRY),'--case','status','--output',str(invalid),'--receipt',str(invalid/'answers.json')],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertFalse(invalid.exists())

    def test_entry_outcome_vocabulary_matches_diagnostic_reference(self):
        entry=(ROOT/'skills/sdd-workflow-router/SKILL.md').read_text(encoding='utf-8')
        model=(ROOT/'skills/sdd-workflow-router/references/routing-model.md').read_text(encoding='utf-8')
        entry_section=entry.split('For diagnostics return one of ')[1].split('; use their')[0]
        model_section=model.split('## 10. Diagnostic procedure')[1].split('## 11.')[0]
        public=set(re.findall(r'`([A-Z_]+)`',entry_section))
        detailed=set(re.findall(r'^\| `([A-Z_]+)` \|',model_section,re.M))
        self.assertEqual(public,detailed)
        self.assertEqual(len(public),5)

    def test_first_use_and_review_entry_links_resolve(self):
        files=[ROOT/'README.md',ROOT/'docs/QUICKSTART.md',ROOT/'docs/DOCTOR.md',ROOT/'docs/OPERATIONS.md',
               ROOT/'docs/REVIEW-FEEDBACK.md',
               *sorted((ROOT/'docs/optimization').glob('*.md')),
               ROOT/'skills/sdd-workflow-router/SKILL.md',
               ROOT/'skills/sdd-workflow-router/evals/forward/entry.md',
               ROOT/'skills/sdd-workflow-router/evals/forward/pilot.md',
               ROOT/'skills/sdd-plan-slices/evals/forward/layout.md']
        checked=0
        for file in files:
            for ref in re.findall(r'(?<!!)\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)',file.read_text(encoding='utf-8')):
                if '://' in ref or ref.startswith('#'):continue
                target=ref.split('#')[0]
                self.assertTrue((file.parent/target).exists(),(file,ref));checked+=1
        self.assertGreater(checked,15)


if __name__=='__main__':unittest.main()
