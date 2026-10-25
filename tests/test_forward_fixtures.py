"""Fixture/oracle integrity; these tests do not execute or score Agent behavior."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
RECOVERY=ROOT/'skills/sdd-verification-design/evals/forward'
REPAIR=ROOT/'skills/sdd-code-review/evals/forward'


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


prepare_recovery=module('prepare_recovery',RECOVERY/'prepare_recovery.py')
prepare_repair=module('prepare_repair',REPAIR/'prepare_repair.py')
probe=module('probe_recovery',RECOVERY/'probe_recovery.py')
repair_probe=module('probe_repair',REPAIR/'probe_repair.py')


class ForwardFixtures(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)

    def test_generated_actor_inputs_are_reproducible_and_exclude_evaluator_assets(self):
        a=prepare_recovery.prepare(self.base/'a','combined')
        b=prepare_recovery.prepare(self.base/'b','combined')
        self.assertEqual(a,b)
        self.assertEqual(set(a),{'AGENTS.md','REQUEST.md','app.py','index.html','notes.txt',
                                 'plan.md','spec.md','state.json','test_baseline.py'})
        self.assertFalse(any('probe' in name or 'receipt' in name or 'variant' in name for name in a))
        with self.assertRaises(ValueError): prepare_recovery.prepare(self.base/'a')

    def test_runtime_snapshot_excludes_evals_tests_and_caches(self):
        hashes=prepare_recovery.snapshot(ROOT/'skills',self.base/'skills')
        self.assertEqual(len([name for name in hashes if name.endswith('/SKILL.md')]),12)
        self.assertFalse(any('/evals/' in name or '/tests/' in name or '__pycache__' in name for name in hashes))
        self.assertIn('sdd-code-review/references/review-model.md',hashes)

    def test_cli_receipt_freezes_input_and_runtime_bytes_outside_actor(self):
        output=self.base/'project';receipt=self.base/'receipt.json';snapshot=self.base/'snapshot'
        result=subprocess.run([sys.executable,'-B',str(RECOVERY/'prepare_recovery.py'),'--output',str(output),
            '--receipt',str(receipt),'--skills',str(ROOT/'skills'),'--snapshot',str(snapshot)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        value=json.loads(receipt.read_text())
        for name,sha in value['inputs'].items():self.assertEqual(hashlib.sha256((output/name).read_bytes()).hexdigest(),sha)
        self.assertEqual(value['skills'],prepare_recovery.hashes(snapshot))
        invalid=subprocess.run([sys.executable,'-B',str(RECOVERY/'prepare_recovery.py'),'--output',str(self.base/'another'),
            '--receipt',str(self.base/'another/receipt.json')],capture_output=True,text=True)
        self.assertNotEqual(invalid.returncode,0)
        self.assertFalse((self.base/'another').exists())
        invalid=subprocess.run([sys.executable,'-B',str(RECOVERY/'prepare_recovery.py'),'--output',str(self.base/'new-project'),
            '--skills',str(ROOT/'skills'),'--snapshot',str(self.base/'new-snapshot'),
            '--receipt',str(self.base/'new-snapshot/receipt.json')],capture_output=True,text=True)
        self.assertNotEqual(invalid.returncode,0)
        self.assertFalse((self.base/'new-project').exists())
        self.assertFalse((self.base/'new-snapshot').exists())

    def test_original_suite_is_green_for_every_variant(self):
        for variant in prepare_recovery.VARIANTS:
            with self.subTest(variant=variant):
                project=self.base/variant;prepare_recovery.prepare(project,variant)
                result=subprocess.run([sys.executable,'-B','-m','unittest','discover'],cwd=project,capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)

    def test_public_http_oracle_detects_loss_without_changing_original_inputs(self):
        for variant in prepare_recovery.VARIANTS:
            with self.subTest(variant=variant):
                project=self.base/variant;before=prepare_recovery.prepare(project,variant)
                checks=probe.observe(project)
                expected_loss=variant in ('lossy','combined')
                for key in ('conflicting_read_rejected','conflicting_append_rejected','attempt_preserves_bytes'):
                    self.assertEqual(checks[key],not expected_loss,(variant,key,checks))
                for key in ('known_records','append_preserves','duplicate_identity_preserves_bytes','non_object_requests_rejected','new_process_restart','missing_state_rejected_without_creation','directory_state_rejected_without_replacement','read_preserves_bytes','source_state_untouched'):
                    self.assertTrue(checks[key],(variant,key,checks))
                self.assertEqual(prepare_recovery.hashes(project),before)

    def test_e5_original_tests_miss_two_observable_contract_failures(self):
        project=self.base/'repair';hashes=prepare_repair.prepare(project)
        result=subprocess.run([sys.executable,'-B','-m','unittest','discover'],cwd=project,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        labels=module('e5_labels',project/'labels.py')
        self.assertEqual(labels.normalize_label('  '),'')
        self.assertEqual(labels.unique_labels([' One ','one','Two']),['One','one','Two'])
        checks=repair_probe.observe(project)
        self.assertFalse(checks['blank_rejected'])
        self.assertFalse(checks['stable_case_insensitive_unique'])
        self.assertFalse(checks['invalid_collection_rejected'])
        self.assertTrue(checks['trim_preserved'])
        self.assertTrue(checks['empty_collection'])
        self.assertEqual(prepare_repair.prepare(self.base/'same'),hashes)
        readonly=prepare_repair.prepare(self.base/'readonly','review-only')
        for name in hashes:
            if name!='REQUEST.md':self.assertEqual(hashes[name],readonly[name])


if __name__=='__main__': unittest.main()
