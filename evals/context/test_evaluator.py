from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tempfile,unittest
from evaluate_view import evaluate,ROOT

class EvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.run=Path(self.tmp.name);self.project=self.run/'project'
        shutil.copytree(ROOT/'skills/sdd-workflow-router/evals/forward/inputs/stage-reading',self.project)
        self.receipt={'project':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in self.project.iterdir()}}
        (self.run/'input-receipt.json').write_text(json.dumps(self.receipt),encoding='utf-8');(self.run/'events.jsonl').write_text('',encoding='utf-8')
    def render(self,nested):
        data={'project_id':'oracle-calibration','title':'Synthetic incomplete board','scope':'not a model run','captured_at':'2026-10-26','items':[]}
        inp=self.project/'input.json';inp.write_text(json.dumps(data),encoding='utf-8');out=self.project/('artifacts/view-v1'if nested else'view-v1')
        p=subprocess.run([sys.executable,'-B',str(ROOT/'skills/sdd-workflow-router/scripts/project_view.py'),'render','--root',str(self.project),'--input',str(inp),'--output',str(out)],capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr);return out
    def test_nested_complete_bundles_are_discovered_but_missing_facts_fail(self):
        out=self.render(True);r=evaluate(self.run);self.assertEqual(r['automated_quality'],'FAIL');self.assertIn('Missing constraint',r['errors']);self.assertEqual(r['latest'],str(out.resolve()))
    def test_source_mutation_is_not_reported_unchanged(self):
        self.render(False);(self.project/'RULES.md').write_text('changed',encoding='utf-8')
        r=evaluate(self.run);self.assertFalse(r['original_sources_unchanged']);self.assertIn('Original input changed',r['errors'])
    def test_changed_bundle_does_not_pass_with_rewritten_observations(self):
        out=self.render(False);(out/'index.html').write_text('changed',encoding='utf-8')
        with self.assertRaises(ValueError):evaluate(self.run)
