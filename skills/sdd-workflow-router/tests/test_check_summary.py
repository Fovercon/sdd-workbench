"""Compact diagnostics must preserve source-check and Unicode behavior."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,tempfile,unittest

CLI=Path(__file__).resolve().parents[1]/'scripts/project_view.py'

class CheckSummaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.source=self.root/'中文.txt';self.source.write_text('original',encoding='utf-8')
        self.data={'project_id':'synthetic','title':'合成诊断','scope':'bounded test','captured_at':'2026-10-26','items':[
            {'id':'记录'+str(n),'label':'合成记录','kind':'assessment','view':'progress','state':'UNKNOWN','note':'正文'*1000,
             'sources':[{'path':'中文.txt','sha256':hashlib.sha256(self.source.read_bytes()).hexdigest(),'line':1}]}for n in range(25)]}
    def run_cli(self,summary=False,command='check',encoding=None):
        p=self.root/'input.json';p.write_text(json.dumps(self.data,ensure_ascii=False),encoding='utf-8')
        args=[sys.executable,'-B',str(CLI),command,'--root',str(self.root),'--input',str(p)]
        if summary:args+=['--summary']
        if command!='check':args+=['--output',str(self.root/'view')]
        env={**os.environ,**({'PYTHONIOENCODING':encoding}if encoding else{})}
        return subprocess.run(args,capture_output=True,env=env)
    def test_summary_keeps_unknown_state_and_full_output_compatibility(self):
        full=self.run_cli();compact=self.run_cli(True)
        self.assertEqual((full.returncode,compact.returncode),(0,0))
        self.assertEqual(len(json.loads(full.stdout)),25)
        report=json.loads(compact.stdout)
        self.assertEqual(report['recorded_state_counts'],{'UNKNOWN':25})
        self.assertEqual(report['freshness_counts'],{'CURRENT':25})
        self.assertEqual(report['noncurrent_count'],0)
        self.assertLess(len(compact.stdout),1200);self.assertGreater(len(full.stdout),100000)
        self.assertEqual(self.source.read_text(encoding='utf-8'),'original')
    def test_stale_and_missing_sources_keep_exit_code_and_explicit_omissions(self):
        for missing in (False,True):
            if missing:self.source.unlink()
            else:self.source.write_text('changed',encoding='utf-8')
            full=self.run_cli();compact=self.run_cli(True);self.assertEqual((full.returncode,compact.returncode),(2,2))
            report=json.loads(compact.stdout);self.assertEqual(report['noncurrent_count'],25)
            self.assertEqual(len(report['noncurrent_ids']),10);self.assertEqual(report['omitted_noncurrent_ids'],15)
            self.assertEqual(report['freshness_counts'],{'UNKNOWN'if missing else'STALE':25})
    def test_long_ids_are_reported_as_truncated(self):
        self.data['items'][0]['id']='x'*10000;self.source.unlink()
        report=json.loads(self.run_cli(True).stdout)
        self.assertTrue(report['truncated_ids']);self.assertEqual(len(report['noncurrent_ids'][0]),160)
    def test_summary_is_not_a_render_mode(self):
        self.assertEqual(self.run_cli(True,'render').returncode,1)
        self.assertFalse((self.root/'view').exists())
    def test_windows_pipe_preserves_full_and_compact_json_and_render(self):
        for summary,command in [(False,'check'),(True,'check'),(False,'render')]:
            run=self.run_cli(summary,command,'cp1252');self.assertEqual(run.returncode,0,run.stderr)
            json.loads(run.stdout.decode('utf-8'));self.assertNotIn(b'UnicodeEncodeError',run.stderr)
    def test_describe_needs_no_project_and_cannot_be_mistaken_for_a_check(self):
        before=set(self.root.iterdir())
        run=subprocess.run([sys.executable,'-B',str(CLI),'describe'],cwd=self.root,capture_output=True)
        self.assertEqual(run.returncode,0,run.stderr)
        contract=json.loads(run.stdout);self.assertIn('no project inspected',contract['purpose'])
        self.assertEqual(len(contract['lifecycle']['stages']),8)
        self.assertIn('command',contract['stage_detail']['Constitution']['command'])
        self.assertIn('delivery_receipt',contract['stage_detail']['Finish']['deliverable'])
        self.assertEqual(contract['work']['brief']['view'],'progress')
        self.assertLess(len(run.stdout),8500);self.assertEqual(set(self.root.iterdir()),before)
    def test_describe_rejects_project_arguments_and_check_still_requires_root(self):
        for command in [['describe','--root',str(self.root)],['check']]:
            run=subprocess.run([sys.executable,'-B',str(CLI),*command],capture_output=True)
            self.assertNotEqual(run.returncode,0)
