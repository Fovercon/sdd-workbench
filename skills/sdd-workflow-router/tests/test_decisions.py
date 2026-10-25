"""Decision drafts bind a concrete question and current sources without approving."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLI = Path(__file__).resolve().parents[1] / 'scripts/project_view.py'
RESPONSE = CLI.with_name('decision_response.py')


class DecisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('plan.md', 'module.md'):
            (self.root / name).write_text(name)
        def ref(name):
            return {'path': name, 'sha256': hashlib.sha256((self.root/name).read_bytes()).hexdigest(), 'line':1}
        self.data = {'project_id':'questions', 'title':'设计评审', 'scope':'本轮设计', 'captured_at':'2026-10-21',
                     'items':[{'id':'gate', 'label':'设计确认', 'view':'progress', 'kind':'assessment',
                               'state':'PENDING_HUMAN', 'sources':[ref('plan.md')],
                               'decision':{'id':'D-01','kind':'approval','prompt':'是否接受这份接口设计？',
                                 'owner':'项目所有者','scope':'只确认所引接口设计。',
                                 'options':[
                                     {'id':'yes','label':'接受','description':'以此为基线。','effect':'APPROVE'},
                                     {'id':'changes','label':'修改','description':'说明修改内容。','effect':'REQUEST_CHANGES','requires_note':True},
                                     {'id':'defer','label':'暂缓','description':'暂不处理。','effect':'DEFER'}]}},
                              {'id':'child','label':'模块设计','view':'progress','kind':'assessment',
                               'state':'PENDING_HUMAN','sources':[ref('module.md')],'decision_ref':'gate'}]}
        self.input = self.root/'input.json'

    def render(self, name='view'):
        self.input.write_text(json.dumps(self.data,ensure_ascii=False))
        return subprocess.run([sys.executable,'-B',str(CLI),'render','--root',str(self.root),
            '--input',str(self.input),'--output',str(self.root/name)],capture_output=True,text=True)

    def response(self):
        return {'schema':'sdd-decision-response/v1','project_id':'questions',
                'snapshot_sha256':hashlib.sha256((self.root/'view/snapshot.json').read_bytes()).hexdigest(),
                'item_id':'gate','decision_id':'D-01','answer':'yes','note':'','origin':'board_draft'}

    def check(self, response):
        f=self.root/'response.json';f.write_text(json.dumps(response))
        return subprocess.run([sys.executable,'-B',str(RESPONSE),'--root',str(self.root),
            '--view',str(self.root/'view'),'--response',str(f)],capture_output=True,text=True)

    def test_one_explicit_question_for_shared_gate_and_no_preselection(self):
        self.assertEqual(self.render().returncode,0)
        page=(self.root/'view/index.html').read_text()
        self.assertEqual(page.count('class="decision-form"'),1)
        self.assertIn('是否接受这份接口设计？',page)
        self.assertIn('data-decision-action="copy"',page)
        self.assertNotIn(' required checked',page)
        self.assertNotIn('待业务决定',page)
        self.assertIn('只确认所引接口设计', (self.root/'view/view.md').read_text())

    def test_validation_is_read_only_and_never_grants_authority(self):
        self.assertEqual(self.render().returncode,0)
        before={p.name:p.read_bytes() for p in (self.root/'view').iterdir()}
        result=self.check(self.response())
        self.assertEqual(result.returncode,0,result.stderr)
        value=json.loads(result.stdout)
        self.assertEqual(value['status'],'RESPONSE_VALIDATED')
        self.assertTrue(value['requires_human_authority'])
        self.assertFalse(value['writes'])
        self.assertEqual({p.name:p.read_bytes() for p in (self.root/'view').iterdir()},before)
        self.assertEqual(json.loads((self.root/'view/snapshot.json').read_text())['items'][0]['state'],'PENDING_HUMAN')

    def test_wrong_identity_choice_and_missing_change_reason_rejected(self):
        self.assertEqual(self.render().returncode,0)
        original=self.response()
        for delta in ({'project_id':'other'},{'snapshot_sha256':'0'*64},{'item_id':'child'},
                      {'decision_id':'other'},{'answer':'invented'},{'answer':'changes','note':''}):
            with self.subTest(delta=delta):
                self.assertEqual(self.check(dict(original,**delta)).returncode,1)
        good=dict(original,answer='changes',note='补充超时与失败返回。')
        self.assertEqual(json.loads(self.check(good).stdout)['effect'],'REQUEST_CHANGES')

    def test_gate_or_linked_source_change_blocks_response_and_controls(self):
        for name in ('plan.md','module.md'):
            with self.subTest(name=name):
                if (self.root/'view').exists():
                    self.tmp.cleanup();self.setUp()
                self.assertEqual(self.render().returncode,0)
                answer=self.response();(self.root/name).write_text('changed')
                self.assertEqual(self.check(answer).returncode,1)
                self.assertEqual(self.render('stale').returncode,2)
                self.assertIn('<fieldset class="decision-fields" disabled>',(self.root/'stale/index.html').read_text())

    def test_tampered_snapshot_or_html_is_rejected(self):
        self.assertEqual(self.render().returncode,0)
        answer=self.response()
        (self.root/'view/index.html').write_text('changed')
        result=self.check(answer)
        self.assertEqual(result.returncode,1)
        self.assertIn('Previous version changed',result.stderr)

    def test_legacy_pending_record_requests_clarification_without_approval_form(self):
        self.data['items']=[self.data['items'][0]]
        self.data['items'][0].pop('decision')
        self.assertEqual(self.render().returncode,0)
        text=(self.root/'view/index.html').read_text()
        self.assertIn('data-copy-clarification',text)
        self.assertNotIn('class="decision-form"',text)

    def test_input_response_and_deferral_have_distinct_effects(self):
        self.assertEqual(self.render().returncode,0)
        response=self.response();response['answer']='defer'
        self.assertEqual(json.loads(self.check(response).stdout)['effect'],'DEFER')
        self.data['items'][0]['decision'].update(kind='input',options=[])
        self.assertEqual(self.render('input').returncode,0)
        response.update(snapshot_sha256=hashlib.sha256((self.root/'input/snapshot.json').read_bytes()).hexdigest(),answer='/path/to/sample.zip')
        f=self.root/'response.json';f.write_text(json.dumps(response))
        run=subprocess.run([sys.executable,'-B',str(RESPONSE),'--root',str(self.root),'--view',str(self.root/'input'),'--response',str(f)],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout)['effect'],'ANSWER')

    def test_malformed_metadata_rejected_before_output(self):
        baseline=copy.deepcopy(self.data)
        changes=[lambda d:d['items'][1].update(decision_ref='absent'),
                 lambda d:d['items'][0]['decision'].update(kind='choice'),
                 lambda d:d['items'][0]['decision'].update(prompt=''),
                 lambda d:d['items'][0]['decision'].update(options=[])]
        for n,change in enumerate(changes):
            self.data=copy.deepcopy(baseline);change(self.data)
            self.assertEqual(self.render(f'bad-{n}').returncode,1)
            self.assertFalse((self.root/f'bad-{n}').exists())

    def test_optional_feedback_is_not_an_approval_gate(self):
        gate=self.data['items'][0]
        gate['state']='GAP'
        gate['decision']['kind']='feedback'
        gate['decision']['options'][0]['effect']='ANSWER'
        self.assertEqual(self.render().returncode,0)
        page=(self.root/'view/index.html').read_text()
        self.assertIn('data-optional-feedback="true"',page)
        self.assertNotIn('<fieldset class="decision-fields" disabled>',page)
        result=self.check(self.response())
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['effect'],'ANSWER')
        self.assertEqual(json.loads((self.root/'view/snapshot.json').read_text())['items'][0]['state'],'GAP')
        gate['decision']['options'][0]['effect']='APPROVE'
        self.assertEqual(self.render('invalid-feedback').returncode,1)


if __name__ == '__main__': unittest.main()
