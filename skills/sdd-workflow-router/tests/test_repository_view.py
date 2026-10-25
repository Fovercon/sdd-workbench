"""A capability is not a source file; repository claims must have file evidence."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLI=Path(__file__).resolve().parents[1]/'scripts/project_view.py'

class RepositoryViewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.data={'project_id':'loan','title':'借用系统','scope':'两个代码文件','captured_at':'2026-10-20','items':[]}
        for name in ['entry','store']:
            path=f'loan/src/{name}.py';p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(name)
            self.data['items'].append({'id':name,'label':name,'view':'structure','kind':'code_observation','state':'SATISFIED',
                'file':path,'sources':[{'path':path,'line':1,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]})
        self.data['items'].append({'id':'call','label':'调用任务处理','view':'structure','kind':'code_observation','state':'SATISFIED',
            'from':'entry','to':'store','sources':copy.deepcopy(self.data['items'][0]['sources'])})
        self.data['items'].append({'id':'retry','label':'重试失败项','view':'capability','kind':'code_observation','state':'SATISFIED',
            'implementation_ids':['store'],'sources':copy.deepcopy(self.data['items'][1]['sources'])})
    def run_view(self,name='view'):
        source=self.root/'input.json';source.write_text(json.dumps(self.data,ensure_ascii=False))
        return subprocess.run([sys.executable,'-B',str(CLI),'render','--root',str(self.root),'--input',str(source),'--output',str(self.root/name)],capture_output=True,text=True)
    def test_functions_map_to_real_files_without_becoming_architecture_nodes(self):
        run=self.run_view();self.assertEqual(run.returncode,0,run.stderr)
        html=(self.root/'view/index.html').read_text()
        self.assertIn('class="repository-map"',html)
        self.assertIn('data-node-id="entry"',html);self.assertNotIn('data-node-id="retry"',html)
        self.assertIn('loan/src/store.py',html)
        self.assertIn('这项功能在哪里实现',html);self.assertIn('这个文件负责的功能',html)
        self.assertIn('data-edge-id="call"',html)
        self.assertIn('重试失败项',(self.root/'view/view.md').read_text())
    def test_file_claim_without_its_source_is_rejected(self):
        self.data['items'][0]['file']='loan/src/fiction.py'
        run=self.run_view();self.assertEqual(run.returncode,1);self.assertFalse((self.root/'view').exists())
    def test_two_nodes_cannot_pretend_to_be_two_files_when_they_share_one(self):
        extra=copy.deepcopy(self.data['items'][0]);extra['id']='another-role';self.data['items'].append(extra)
        run=self.run_view();self.assertEqual(run.returncode,1);self.assertFalse((self.root/'view').exists())
    def test_invalid_implementation_link_is_rejected(self):
        baseline=copy.deepcopy(self.data)
        for bad in [['absent'],['call'],['retry'],'store']:
            self.data=copy.deepcopy(baseline);self.data['items'][-1]['implementation_ids']=bad
            run=self.run_view();self.assertEqual(run.returncode,1);self.assertNotIn('Traceback',run.stderr)
    def test_implementation_mapping_must_cite_that_file(self):
        self.data['items'][-1]['sources']=copy.deepcopy(self.data['items'][0]['sources'])
        run=self.run_view();self.assertEqual(run.returncode,1)
    def test_source_change_invalidates_file_and_mapped_function(self):
        (self.root/'loan/src/store.py').write_text('changed')
        run=self.run_view();self.assertEqual(run.returncode,2,run.stderr)
        receipt=json.loads((self.root/'view/receipt.json').read_text())
        states={i['id']:i['effective_state'] for i in receipt['items']}
        self.assertEqual(states['store'],'STALE');self.assertEqual(states['retry'],'STALE')
    def test_cycle_remains_explicit_and_is_not_rendered_as_a_pipeline(self):
        edge=copy.deepcopy(self.data['items'][2]);edge.update(id='back',**{'from':'store','to':'entry'})
        self.data['items'].append(edge)
        run=self.run_view();self.assertEqual(run.returncode,0,run.stderr)
        html=(self.root/'view/index.html').read_text()
        self.assertNotIn('class="file-flow"',html)
        for key in ['call','back']:self.assertIn(f'data-edge-id="{key}"',html)
        for key in ['entry','store']:self.assertIn(f'data-node-id="{key}"',html)

if __name__=='__main__':unittest.main()
