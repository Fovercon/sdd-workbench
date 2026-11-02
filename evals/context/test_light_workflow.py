import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest
from unittest.mock import patch

import prepare_workflow
from prepare_workflow import prepare
from evaluate_workflow import evaluate


class LightWorkflowTests(unittest.TestCase):
    def test_matched_ref_and_visible_primary_clauses(self):
        with tempfile.TemporaryDirectory() as d:
            repo=Path(d)/'source';repo.mkdir()
            original_root=Path(__file__).resolve().parents[2]
            shutil.copytree(original_root/'evals/context/inputs/implement',repo/'evals/context/inputs/implement')
            skill=repo/'skills/sdd-implement-slice/SKILL.md';skill.parent.mkdir(parents=True)
            skill.write_text('Committed fixture skill bytes\n')
            subprocess.run(['git','init','-b','codex/protocol-fixture'],cwd=repo,check=True,capture_output=True)
            subprocess.run(['git','add','.'],cwd=repo,check=True,capture_output=True)
            subprocess.run(['git','-c','user.name=Eval','-c','user.email=eval@example.invalid','-c','commit.gpgsign=false','commit','-m','Fixture'],cwd=repo,check=True,capture_output=True)
            revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
            skill.write_text('Uncommitted candidate skill bytes\n')
            old, new = Path(d)/'old', Path(d)/'new'
            with patch.object(prepare_workflow,'ROOT',repo):
                prepare('visible', old, ref='HEAD')
                prepare('visible', new)
            self.assertEqual((old/'prompt.txt').read_bytes(), (new/'prompt.txt').read_bytes())
            a=json.loads((old/'input-receipt.json').read_text())
            b=json.loads((new/'input-receipt.json').read_text())
            self.assertEqual(a['project'], b['project'])
            self.assertEqual((old/'runtime/sdd-implement-slice/SKILL.md').read_bytes(),b'Committed fixture skill bytes\n')
            self.assertEqual((new/'runtime/sdd-implement-slice/SKILL.md').read_bytes(),b'Uncommitted candidate skill bytes\n')
            prompt=(old/'prompt.txt').read_text()
            for name in ('AGENTS.md','SPEC.md','PLAN.md','CURRENT-CARD.md'):
                data=(old/'project'/name).read_bytes()
                self.assertIn(data.decode(), prompt)
                self.assertIn(hashlib.sha256(data).hexdigest(), prompt)
            self.assertEqual(json.loads((old/'variant.json').read_text())['source'],revision)
            with self.assertRaises(ValueError): prepare('visible', old)

    def test_direct_accepts_repair_and_detects_protected_edits(self):
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/'trial';prepare('direct',run)
            (run/'project/service.py').write_text("def select(items,key):\n return [x for x in items if x['id']==key]\n")
            self.assertEqual(evaluate('direct',run)['automated_guards'],'PASS')
            (run/'project/user-notes.txt').write_text('lost user notes')
            self.assertIn('Protected input changed',evaluate('direct',run)['errors'])

    def test_direct_rejects_original_bug_and_flags_extra_ceremony(self):
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/'trial';prepare('direct',run)
            self.assertIn('Independent behavior probe:',str(evaluate('direct',run)['errors']))
            (run/'project/service.py').write_text("def select(items,key):\n return [x for x in items if x['id']==key]\n")
            (run/'project/SPEC.md').write_text('unsolicited contract')
            self.assertIn('SPEC.md',evaluate('direct',run)['unexpected_outputs'])

    def test_risk_checks_read_only_and_frozen_runtime_including_additions(self):
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)/'trial';prepare('risk',run)
            self.assertEqual(evaluate('risk',run)['automated_guards'],'PASS')
            (run/'runtime/extra.py').write_text('untracked runtime change')
            self.assertIn('Runtime modified',evaluate('risk',run)['errors'])
            (run/'project/service.py').write_text('changed security behavior')
            self.assertIn('Protected input changed',evaluate('risk',run)['errors'])


if __name__=='__main__':unittest.main()
