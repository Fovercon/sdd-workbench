"""Portable view contracts: versions, evidence identity, layout completeness and safety."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLI = Path(__file__).resolve().parents[1] / 'scripts/project_view.py'

class ProjectViewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name);(self.root/'source.txt').write_text('登记和归还设备',encoding='utf-8')
        self.ref = {'path':'source.txt','line':1,'sha256':hashlib.sha256((self.root/'source.txt').read_bytes()).hexdigest()}
        def item(i,label,view='structure',state='SATISFIED'):
            return {'id':i,'label':label,'view':view,'state':state,'kind':'code_observation','sources':[self.ref],'note':'现有证据','next':''}
        self.data={'project_id':'equipment','title':'设备借用','scope':'登记和归还','captured_at':'2026-10-19','items':[item('done','登记已验证','progress'),item('decision','归还期限待决定','progress','PENDING_HUMAN'),item('register','登记'),item('return','归还')]}
        self.data['items'].append(dict(item('flow','关联已登记设备'),**{'from':'register','to':'return'}))
        self.input=self.root/'input.json';self.save()
    def save(self):self.input.write_text(json.dumps(self.data,ensure_ascii=False),encoding='utf-8')
    def run_cli(self,*args):
        return subprocess.run([sys.executable,'-B',str(CLI),*map(str,args),'--root',str(self.root)],capture_output=True,text=True)
    def create(self,name='v1'):
        run=self.run_cli('render','--input',self.input,'--output',self.root/name)
        self.assertEqual(run.returncode,0,run.stderr);return self.root/name
    def receipt(self,path):return json.loads((path/'receipt.json').read_text())
    def test_self_contained_bundle_has_clickable_graph_and_bound_fingerprints(self):
        before=self.input.read_bytes();v=self.create();html=(v/'index.html').read_text();receipt=self.receipt(v)
        self.assertIn('data-node-id="register"',html);self.assertIn('data-edge-id="flow"',html)
        self.assertNotIn('company-view',html);self.assertNotIn('governance',html)
        self.assertEqual((v/'snapshot.json').read_bytes(),before);self.assertEqual(self.input.read_bytes(),before)
        self.assertEqual(receipt['project_id'],'equipment');self.assertIsNone(receipt['previous'])
        for name,digest in receipt['files'].items():self.assertEqual(hashlib.sha256((v/name).read_bytes()).hexdigest(),digest)
    def test_recheck_update_retains_old_judgment_and_invalidates_related_edge(self):
        v=self.create();old={p.name:p.read_bytes() for p in v.iterdir()};(self.root/'source.txt').write_text('changed')
        run=self.run_cli('update','--previous',v,'--output',self.root/'v2')
        self.assertEqual(run.returncode,2,run.stderr)
        self.assertEqual({p.name:p.read_bytes() for p in v.iterdir()},old)
        r=self.receipt(self.root/'v2');self.assertTrue(all(i['freshness']=='STALE' for i in r['items']))
        self.assertEqual(json.loads((self.root/'v2/snapshot.json').read_text()),self.data)
        html=(self.root/'v2/index.html').read_text();self.assertIn('重新核对来源',html);self.assertIn('../v1/index.html',html)
        self.assertEqual(r['previous']['receipt_sha256'],hashlib.sha256((v/'receipt.json').read_bytes()).hexdigest())
    def test_missing_source_becomes_unknown_without_rewriting_digest(self):
        v=self.create();(self.root/'source.txt').unlink();run=self.run_cli('update','--previous',v,'--output',self.root/'v2')
        self.assertEqual(run.returncode,2,run.stderr);r=self.receipt(self.root/'v2')
        self.assertTrue(all(i['effective_state']=='UNKNOWN' for i in r['items']))
        self.assertEqual(json.loads((self.root/'v2/snapshot.json').read_text())['items'][0]['sources'][0]['sha256'],self.ref['sha256'])
    def test_reassessment_requires_reason_and_reports_change_set(self):
        v=self.create();self.data['items'][1]['state']='SATISFIED';self.data['items'][1]['note']='业务决定见现有来源';self.save()
        args=['update','--previous',v,'--input',self.input,'--output',self.root/'v2']
        run=self.run_cli(*args);self.assertEqual(run.returncode,1);self.assertFalse((self.root/'v2').exists())
        run=self.run_cli(*args,'--reason','重新核对已记录的决定');self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(self.receipt(self.root/'v2')['changes']['modified'],['decision'])
    def test_update_rejects_another_project_identity(self):
        v=self.create();self.data['project_id']='unrelated';self.save()
        run=self.run_cli('update','--previous',v,'--input',self.input,'--reason','changed','--output',self.root/'v2')
        self.assertEqual(run.returncode,1);self.assertFalse((self.root/'v2').exists())
    def test_parent_tampering_prevents_update(self):
        v=self.create();(v/'index.html').write_text('tampered')
        run=self.run_cli('update','--previous',v,'--output',self.root/'v2')
        self.assertEqual(run.returncode,1);self.assertFalse((self.root/'v2').exists())
    def test_existing_output_and_symlink_never_overwritten(self):
        v=self.create();before=(v/'index.html').read_bytes()
        for target in [v,self.root/'alias']:
            if target.name=='alias':target.symlink_to(v,target_is_directory=True)
            run=self.run_cli('render','--input',self.input,'--output',target)
            self.assertEqual(run.returncode,1);self.assertEqual((v/'index.html').read_bytes(),before)
    def test_nested_update_must_not_modify_old_version_directory(self):
        v=self.create();run=self.run_cli('update','--previous',v,'--output',v/'v2')
        self.assertEqual(run.returncode,1);self.assertFalse((v/'v2').exists())
    def test_path_escape_and_symlink_escape_are_rejected(self):
        for bad in ['../outside.txt','escape.txt']:
            if bad=='escape.txt':(self.root/bad).symlink_to('/etc/passwd')
            self.data['items'][0]['sources'][0]['path']=bad;self.save()
            run=self.run_cli('render','--input',self.input,'--output',self.root/'bad')
            self.assertEqual(run.returncode,1);self.assertFalse((self.root/'bad').exists())
    def test_invalid_endpoint_is_rejected_before_writing(self):
        self.data['items'][-1]['to']='absent';self.save();run=self.run_cli('render','--input',self.input,'--output',self.root/'bad')
        self.assertEqual(run.returncode,1);self.assertFalse((self.root/'bad').exists())
    def test_unanchored_claim_cannot_become_satisfied(self):
        self.data['items'][0]['sources']=[];self.save();run=self.run_cli('render','--input',self.input,'--output',self.root/'v1')
        self.assertEqual(run.returncode,2);self.assertEqual(self.receipt(self.root/'v1')['items'][0]['effective_state'],'UNKNOWN')
    def test_empty_and_large_graph_preserve_all_records(self):
        node=copy.deepcopy(self.data['items'][2])
        for count in [0,1,15]:
            self.data['items']=[dict(copy.deepcopy(node),id=f'n{i}',label=f'模块{i}',group='子系统' if i else '') for i in range(count)]
            self.save();v=self.create(f'v{count}');html=(v/'index.html').read_text()
            for i in range(count):self.assertIn(f'data-node-id="n{i}"',html);self.assertIn(f'id="item-n{i}"',html)
    def test_cycle_and_cross_group_relations_stay_navigable(self):
        self.data['items'][2]['group']='前台';self.data['items'][3]['group']='后台'
        self.data['items'].append(dict(copy.deepcopy(self.data['items'][-1]),id='reverse',**{'from':'return','to':'register'}));self.save()
        html=(self.create()/'index.html').read_text()
        for item in self.data['items'][2:]:self.assertIn(f'id="item-{item["id"]}"',html)
        self.assertIn('登记 → 归还',html);self.assertIn('归还 → 登记',html)
    def test_malicious_labels_are_data_and_script_hash_matches(self):
        import base64,re
        self.data['items'][2]['label']='</script><script>globalThis.BAD=true</script>';self.save()
        html=(self.create()/'index.html').read_text();scripts=re.findall(r'<script>(.*?)</script>',html,re.S)
        self.assertEqual(len(scripts),1);self.assertNotIn('<script>globalThis.BAD',html)
        self.assertIn('sha256-'+base64.b64encode(hashlib.sha256(scripts[0].encode()).digest()).decode(),html)
    def test_malformed_input_gives_clean_error_without_output(self):
        self.input.write_text('[]');run=self.run_cli('render','--input',self.input,'--output',self.root/'bad')
        self.assertEqual(run.returncode,1);self.assertNotIn('Traceback',run.stderr);self.assertFalse((self.root/'bad').exists())
    def test_selected_next_action_beats_a_deferred_human_decision(self):
        self.data['items'][0].update(id='integration',label='入口集成验证',state='GAP',next='补充入口集成验证。')
        self.data['next_id']='integration';self.save();html=(self.create()/'index.html').read_text()
        from html.parser import HTMLParser
        class NextTitle(HTMLParser):
            def handle_starttag(self,tag,attrs):
                if dict(attrs).get('id')=='next-title':self.capture=True
            def handle_endtag(self,tag):
                if tag=='h2':self.capture=False
            def handle_data(self,data):
                if getattr(self,'capture',False):self.text=getattr(self,'text','')+data
        parsed=NextTitle();parsed.feed(html);self.assertEqual(parsed.text,'入口集成验证')
        self.assertIn('data-default="integration"',html)
    def test_invalid_explicit_next_action_is_rejected(self):
        self.data['next_id']='absent';self.save();run=self.run_cli('render','--input',self.input,'--output',self.root/'bad')
        self.assertEqual(run.returncode,1);self.assertFalse((self.root/'bad').exists())
    def test_next_action_caption_is_independent_of_completed_record_and_cannot_hide_stale_source(self):
        self.data['items'][0].update(next='打开示例了解如何使用。',next_label='查看运行示例')
        self.data['next_id']='done';self.save()
        html=(self.create()/'index.html').read_text()
        self.assertIn('<h2 id="next-title">查看运行示例</h2>',html)
        (self.root/'source.txt').write_text('changed')
        run=self.run_cli('update','--previous',self.root/'v1','--output',self.root/'v2')
        self.assertEqual(run.returncode,2)
        html=(self.root/'v2/index.html').read_text()
        self.assertIn('<h2 id="next-title">重新核对来源</h2>',html)
    def test_completed_record_navigation_does_not_claim_unfinished_work(self):
        for index,(state,other_state,expected) in enumerate([
            ('SATISFIED','SATISFIED','查看当前记录'),
            ('NOT_APPLICABLE','SATISFIED','查看当前记录'),
            ('GAP','SATISFIED','仍有工作待完成'),
            ('PENDING_HUMAN','SATISFIED','有待确认的事项'),
            ('SATISFIED','GAP','仍有工作待完成'),
        ]):
            with self.subTest(state=state,other_state=other_state):
                self.data['items'][0].update(state=state,next='查看运行证据与样例。')
                self.data['items'][1]['state']=other_state
                self.data['next_id']='done';self.save()
                html=(self.create(f'next-{index}')/'index.html').read_text()
                banner=html.split('<section class="next-action"',1)[1].split('</section>',1)[0]
                self.assertIn(expected,banner)
                self.assertIn('查看运行证据与样例。',banner)
                self.assertIn('data-select="done"',banner)
                if expected=='查看当前记录':self.assertNotIn('仍有工作待完成',banner)
    def test_planned_module_is_identified_as_design_on_map(self):
        self.data['items'][2]['kind']='design';self.data['items'][2]['state']='GAP';self.save()
        html=(self.create()/'index.html').read_text()
        from html.parser import HTMLParser
        class Nodes(HTMLParser):
            def handle_starttag(self,tag,attrs):
                d=dict(attrs)
                if d.get('data-node-id')=='register':self.node=d
        parsed=Nodes();parsed.feed(html)
        self.assertEqual(parsed.node.get('data-kind'),'design')
        self.assertEqual(parsed.node['data-state'],'GAP')
    def test_empty_view_does_not_claim_sources_verified(self):
        self.data['items']=[];self.save();html=(self.create()/'index.html').read_text()
        self.assertNotIn('所列来源已核验',html)
    def test_invalid_parent_receipt_is_a_clean_error(self):
        v=self.create();(v/'receipt.json').write_text('[]')
        run=self.run_cli('update','--previous',v,'--output',self.root/'v2')
        self.assertEqual(run.returncode,1);self.assertNotIn('Traceback',run.stderr)
        self.assertFalse((self.root/'v2').exists())
    def test_check_is_read_only(self):
        before={p.name:p.read_bytes() for p in self.root.iterdir()};run=self.run_cli('check','--input',self.input)
        self.assertEqual(run.returncode,0,run.stderr);self.assertEqual({p.name:p.read_bytes() for p in self.root.iterdir()},before)

    def test_reading_layer_keeps_modules_and_gaps_visible_with_technical_details_closed(self):
        """Disclosure must reduce noise without hiding planned work or losing evidence."""
        from html.parser import HTMLParser
        self.data['items'][2].update(kind='design',state='GAP')
        self.save();html=(self.create()/'index.html').read_text()
        class Disclosure(HTMLParser):
            def __init__(self):
                super().__init__();self.stack=[];self.modules={};self.closed=[];self.sources=[];self.records=[]
            def handle_starttag(self,tag,attrs):
                attrs=dict(attrs);classes=attrs.get('class','').split()
                if tag=='details':
                    self.stack.append('open' not in attrs)
                    if 'open' not in attrs:self.closed.extend(classes)
                if 'module-link' in classes:self.modules[attrs['data-select']]=(attrs,any(self.stack))
                if 'source-link' in classes:self.sources.append(any(self.stack))
                if 'detail-content' in classes:self.records.append(attrs)
            def handle_endtag(self,tag):
                if tag=='details':self.stack.pop()
        parsed=Disclosure();parsed.feed(html)
        self.assertEqual(set(parsed.modules),{'register','return'})
        self.assertTrue(all(not hidden for _,hidden in parsed.modules.values()))
        self.assertEqual(parsed.modules['register'][0]['data-state'],'GAP')
        self.assertEqual(parsed.modules['register'][0]['data-kind'],'design')
        self.assertIn('technical-map',parsed.closed);self.assertIn('evidence',parsed.closed)
        self.assertTrue(parsed.sources and all(parsed.sources))
        self.assertEqual(len(parsed.records),len(self.data['items']))
        self.assertTrue(all('hidden' not in record for record in parsed.records)) # no-JS links remain usable
        self.assertNotIn('<section class="impact"',html) # no empty placeholder section

if __name__=='__main__':unittest.main()
