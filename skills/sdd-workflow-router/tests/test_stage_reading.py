"""Stage detail contracts must preserve authority and source uncertainty."""
import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from stage_reading_fixture import fixture

CLI=Path(__file__).resolve().parents[1]/'scripts/project_view.py'


class StageReadingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.data=fixture(self.root)
    def item(self,key):return next(i for i in self.data['items'] if i['id']==key)
    def render(self,name='view'):
        p=self.root/'input.json';p.write_text(json.dumps(self.data,ensure_ascii=False))
        return subprocess.run([sys.executable,'-B',str(CLI),'render','--root',str(self.root),'--input',str(p),'--output',str(self.root/name)],capture_output=True,text=True)
    def test_four_sections_are_source_bound_and_plain_text_preserved(self):
        self.assertEqual(self.render().returncode,0)
        html=(self.root/'view/index.html').read_text();plain=(self.root/'view/view.md').read_text()
        for text in ['项目约束','开发与检查命令','假设与核实情况','任务与实现文件','测试与运行记录','交付物','已准备，待交付','有交付记录','接续工作','恢复与回退方法']:
            self.assertIn(text,html);self.assertIn(text,plain) if text in ('有交付记录','已准备，待交付') else None
        self.assertIn('python3 -m unittest test_preservation',plain)
        self.assertIn(r'delivery\-receipt\.json',plain)
        self.assertEqual(json.loads((self.root/'view/snapshot.json').read_text()),self.data)
    def test_malformed_types_and_wrong_stage_are_rejected_before_output(self):
        baseline=copy.deepcopy(self.data)
        variants=[('rule',[]),('rule',{'type':'deliverable'}),('rule',{'type':'unknown'}),('run-pass',{'type':'test_run','result':'skip'}),('rule',{'type':'constraint','result':'PASS'}),('usage',{'type':'usage','steps':[]}),('handoff',{'type':'handoff','owner':7})]
        for n,(key,value) in enumerate(variants):
            self.data=copy.deepcopy(baseline);self.item(key)['stage_detail']=value
            self.assertEqual(self.render(str(n)).returncode,1)
            self.assertFalse((self.root/str(n)).exists())
    def test_execution_and_delivery_cannot_be_inferred_from_files(self):
        for n,key in enumerate(['run-pass','delivered']):
            self.item(key)['kind']='assessment'
            self.assertEqual(self.render(str(n)).returncode,1)
            self.item(key)['kind']='runtime_evidence'
        self.item('delivered')['stage_detail'].pop('delivery_receipt')
        self.assertEqual(self.render('no-receipt').returncode,1)
    def test_uncited_or_escaping_deliverable_and_cwd_are_rejected(self):
        baseline=copy.deepcopy(self.data)
        for n,(key,field,value) in enumerate([('candidate','path','other.md'),('candidate','delivery_receipt','delivery-receipt.json'),('planned','path','../outside.md'),('usage','cwd','/tmp'),('delivered','delivery_receipt','delivered.md')]):
            self.data=copy.deepcopy(baseline);self.item(key)['stage_detail'][field]=value
            self.assertEqual(self.render(str(n)).returncode,1)
    def test_missing_sources_and_explanation_rejected(self):
        baseline=copy.deepcopy(self.data)
        for n,change in enumerate([{'sources':[]},{'note':''},{'work':{'type':'brief','in_scope':[],'out_of_scope':[]}}]):
            self.data=copy.deepcopy(baseline);self.item('rule').update(change)
            self.assertEqual(self.render(str(n)).returncode,1)
    def test_dangling_and_cyclic_cross_record_dependencies_rejected(self):
        self.item('run-pass')['stage_detail']['record_ids']=['missing']
        self.assertEqual(self.render('missing').returncode,1)
        self.item('run-pass')['stage_detail']['record_ids']=['candidate']
        self.assertEqual(self.render('cycle').returncode,1)
    def test_changed_related_source_invalidates_passing_run_and_candidate(self):
        (self.root/'component-1.py').write_text('changed implementation')
        self.assertEqual(self.render().returncode,2)
        receipt=json.loads((self.root/'view/receipt.json').read_text());nodes={i['id']:i for i in receipt['items']}
        for key in ['run-pass','candidate']:self.assertEqual(nodes[key]['effective_state'],'STALE')
        self.assertIn('来源已变化，需要重新核对本记录。',(self.root/'view/index.html').read_text())
    def test_missing_delivery_receipt_is_not_current_delivery(self):
        (self.root/'delivery-receipt.json').unlink()
        self.assertEqual(self.render().returncode,2)
        nodes=json.loads((self.root/'view/receipt.json').read_text())['items']
        self.assertEqual(next(i for i in nodes if i['id']=='delivered')['effective_state'],'UNKNOWN')
    def test_delivery_receipt_path_alias_cannot_replace_an_independent_receipt(self):
        record=self.item('delivered');record['stage_detail']['delivery_receipt']='./delivered.md'
        ref=copy.deepcopy(next(r for r in record['sources']if r['path']=='delivered.md'))
        ref['path']='./delivered.md';record['sources'].append(ref)
        self.assertEqual(self.render('alias').returncode,1)
    def test_delivery_receipt_symlink_cannot_point_to_the_output(self):
        (self.root/'delivery-receipt.json').unlink()
        try:(self.root/'delivery-receipt.json').symlink_to(self.root/'delivered.md')
        except OSError:self.skipTest('symlink unavailable on this host')
        self.assertEqual(self.render('symlink').returncode,1)
    def test_delivery_receipt_hardlink_is_not_an_independent_file(self):
        import os
        (self.root/'delivery-receipt.json').unlink()
        os.link(self.root/'delivered.md',self.root/'delivery-receipt.json')
        self.assertEqual(self.render('hardlink').returncode,1)
    def test_upstream_return_keeps_historical_results_and_requires_review(self):
        self.data['lifecycle']['current_stage']='Align'
        self.assertEqual(self.render().returncode,0)
        html=(self.root/'view/index.html').read_text()
        self.assertIn('原记录中的运行结果',html);self.assertIn('原记录中的交付状态',html)
        self.assertIn('本记录或关联记录仍需核对',html)
    def test_absent_detail_is_explicit_and_legacy_records_are_kept(self):
        self.data['items']=[i for i in self.data['items'] if 'stage_detail' not in i]
        self.assertEqual(self.render().returncode,0)
        html=(self.root/'view/index.html').read_text()
        self.assertIn('尚未提供交付物记录',html);self.assertIn('尚未提供具体约束',html)
        self.assertIn('data-select="Finish"',html)
    def test_untrusted_command_and_steps_remain_text(self):
        self.item('usage')['stage_detail']['command']='<img src=x onerror=alert(1)>'
        self.assertEqual(self.render().returncode,0)
        html=(self.root/'view/index.html').read_text()
        self.assertIn('&lt;img src=x onerror=alert(1)&gt;',html);self.assertNotIn('<img src=x',html)
    def test_clarification_keeps_answered_records_without_calling_them_pending(self):
        question=next(i for i in self.data['items'] if i.get('stage')=='Align' and 'decision' in i)
        question['state']='SATISFIED'
        self.assertEqual(self.render().returncode,0)
        html=(self.root/'view/index.html').read_text()
        self.assertIn('确认事项与答复',html)
        self.assertNotIn('<h3>待确认事项</h3>',html)
        self.assertIn('data-select="'+question['id']+'"',html)
