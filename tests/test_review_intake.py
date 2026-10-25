"""Multi-review evidence/provenance, not identity authentication or model judging."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import package


def inventory(root):
    return {p.relative_to(root).as_posix():('link',os.readlink(p)) if p.is_symlink() else
            ('file',p.read_bytes(),p.stat().st_mtime_ns) if p.is_file() else ('dir',p.stat().st_mtime_ns)
            for p in root.rglob('*')}


class ReviewIntake(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name).resolve();self.source=self.base/'source';self.reviews=self.base/'reviews'
        self.reviews.mkdir();(self.reviews/'evidence').mkdir()
        for name,data in package.bundle_files(ROOT).items():
            path=self.source/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)

    def cli(self,*args,expected=0):
        before=inventory(self.base)
        r=subprocess.run([sys.executable,str(self.source/'tools/review.py'),*args],capture_output=True,text=True)
        self.assertEqual(inventory(self.base),before,'review tooling mutated source/reports/evidence/cache')
        self.assertEqual(r.returncode,expected,r.stdout+r.stderr)
        self.assertNotIn('Traceback',r.stderr)
        return json.loads(r.stdout)

    def draft(self,identifier='alice',reviewer='alice'):
        return self.cli('new','--source',str(self.source),'--id',identifier,'--reviewer',reviewer,'--kind','agent')

    def evidence(self,name='log.txt',content='Observed failure; synthetic data.\n'):
        p=self.reviews/'evidence'/name;p.write_text(content)
        return {'path':'evidence/'+name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

    def report(self,identifier='alice',reviewer='alice',finding=True):
        value=self.draft(identifier,reviewer);value.update(status='SUBMITTED',task='Inspect job behavior',notes='Actual observations and limits recorded.')
        if finding:
            value['findings']=[{'id':'F1','title':'Wrong error','severity':'P1','scope':['tools/install.py'],
                'expectation':'Reject unknown state with ValueError','expectation_source':'Synthetic approved contract FR-1',
                'observation':'A public invalid input raised TypeError','consequence':'Caller error contract violated',
                'steps':['python -B test_jobs.py'], 'evidence':[self.evidence()]}]
        return value

    def save(self,value):
        p=self.reviews/(value['id']+'.sdd-review.json');p.write_text(json.dumps(value));return p

    def check(self,*reports,expected=0):
        return self.cli('check','--source',str(self.source),'--report',*(str(p) for p in reports),expected=expected)

    def followup(self,identifier,action,candidate=None,reviewer=None):
        value=self.report(identifier,reviewer or identifier,finding=False)
        if candidate:value['candidate']=candidate
        value['followups']=[{'id':'E1','target':'alice/F1','action':action,'reason':'Synthetic reproducible follow-up',
                             'evidence':[self.evidence(identifier+'.txt')]}]
        return value

    def test_snapshot_is_portable_and_covers_untracked_release_inputs(self):
        a=self.cli('snapshot','--source',str(self.source))
        other=self.base/'copy';shutil.copytree(self.source,other)
        b=self.cli('snapshot','--source',str(other));self.assertEqual(a,b)
        self.assertEqual(a['scope'],'RELEASE_INPUTS');self.assertIn('tools/review.py',a['files'])
        (other/'tools/new-helper.py').write_text('# not tracked\n')
        c=self.cli('snapshot','--source',str(other));self.assertNotEqual(a['fingerprint'],c['fingerprint'])
        self.assertEqual(a['declared_version'],c['declared_version'])

    def test_draft_does_not_count_as_submitted_or_establish_readiness(self):
        p=self.save(self.draft());result=self.check(p)
        self.assertEqual(result['drafts'],1);self.assertEqual(result['submitted_reports'],0)
        self.assertEqual(result['findings'],[]);self.assertEqual(result['release_readiness'],'NOT_ASSESSED')
        self.assertFalse(result['commands_executed']);self.assertFalse(result['identity_authenticated'])

    def test_report_and_evidence_descriptor_are_read_only_without_running_commands(self):
        report=self.report();marker=self.base/'must-not-exist'
        report['inputs']=[self.evidence('REQUEST.txt','Synthetic supplied task input\n')]
        report['findings'][0]['steps']=[f'python -c "open({str(marker)!r},\"w\").write(\"bad\")"']
        p=self.save(report);result=self.check(p)
        self.assertFalse(marker.exists());self.assertEqual(result['findings'][0]['status'],'OPEN')
        descriptor=self.cli('evidence','--root',str(self.reviews),'--path','evidence/log.txt')
        self.assertEqual(descriptor,report['findings'][0]['evidence'][0])
        self.assertEqual(result['reports'][0]['sha256'],hashlib.sha256(p.read_bytes()).hexdigest())

    def test_changed_or_missing_evidence_rejects_the_report(self):
        p=self.save(self.report());(self.reviews/'evidence/log.txt').write_text('tampered')
        self.check(p,expected=2);(self.reviews/'evidence/log.txt').unlink();self.check(p,expected=2)

    def test_unsafe_paths_never_read_outside_evidence(self):
        report=self.report();p=self.save(report)
        for path in ('../outside','/etc/passwd','evidence/../../outside','evidence\\outside','tools/install.py'):
            with self.subTest(path=path):
                invalid=copy.deepcopy(report);invalid['findings'][0]['evidence'][0]['path']=path;p.write_text(json.dumps(invalid))
                self.check(p,expected=2)

    @unittest.skipIf(sys.platform=='win32','Symlink creation may require privileges')
    def test_evidence_links_are_rejected_even_when_bytes_match(self):
        report=self.report();p=self.save(report)
        log=self.reviews/'evidence/log.txt';outside=self.base/'outside';outside.write_bytes(log.read_bytes());log.unlink();log.symlink_to(outside)
        self.check(p,expected=2)
        log.unlink();(self.reviews/'evidence').rmdir()
        directory=self.base/'linked-directory';directory.mkdir();(directory/'log.txt').write_bytes(outside.read_bytes())
        (self.reviews/'evidence').symlink_to(directory,target_is_directory=True)
        self.check(p,expected=2)
        alias=self.reviews/'alias.sdd-review.json';alias.symlink_to(p)
        self.check(alias,expected=2)

    def test_current_recheck_stales_after_source_changes_without_rewriting_report(self):
        original=self.save(self.report());fix=self.save(self.followup('bob','RECHECK_PASS'))
        fresh=self.check(original,fix)
        self.assertEqual(fresh['findings'][0]['status'],'RECHECK_REPORTED')
        self.assertFalse(fresh['automatic_closure'])
        (self.source/'tools/new-helper.py').write_text('# changed candidate\n')
        stale=self.check(original,fix)
        self.assertEqual(stale['findings'][0]['status'],'STALE_RECHECK')
        self.assertTrue(all(not r['matches_current_candidate'] for r in stale['reports']))

    def test_conflicting_current_rechecks_are_disputed_regardless_of_vote_count(self):
        inputs=[self.save(self.report())]
        for identifier,action in [('b','RECHECK_PASS'),('c','RECHECK_PASS'),('d','RECHECK_FAIL')]:
            inputs.append(self.save(self.followup(identifier,action)))
        result=self.check(*inputs);self.assertEqual(result['findings'][0]['status'],'DISPUTED')
        self.assertEqual(result,self.check(*reversed(inputs)))

    def test_self_recheck_and_different_ids_do_not_authenticate_independence(self):
        original=self.save(self.report());follow=self.followup('author2','RECHECK_PASS',reviewer='alice')
        follow['reviewer']['relation']='author';p=self.save(follow)
        result=self.check(original,p);entry=result['findings'][0]['followups'][0]
        self.assertTrue(entry['self_recheck_declared']);self.assertFalse(result['identity_authenticated'])
        self.assertEqual(entry['reviewer']['context'],'unknown')
        # A person rechecking their own finding may still be someone other than
        # the implementer; matching reporter IDs cannot decide authorship.
        follow['reviewer']['relation']='other';p.write_text(json.dumps(follow))
        entry=self.check(original,p)['findings'][0]['followups'][0]
        self.assertTrue(entry['same_reporter_id']);self.assertFalse(entry['self_recheck_declared'])

    def test_duplicates_are_proposals_and_preserve_both_original_findings(self):
        a=self.save(self.report());b=self.report('bob','bob');p=self.save(b)
        link=self.report('triage','triage',finding=False)
        link['followups']=[{'id':'D1','target':'bob/F1','action':'DUPLICATE_PROPOSED','duplicate_of':'alice/F1',
                            'reason':'Same hypothesized cause; not adjudicated','evidence':[]}]
        result=self.check(a,p,self.save(link));self.assertEqual(len(result['findings']),2)
        self.assertEqual({f['status'] for f in result['findings']},{'OPEN'})
        self.assertEqual(result['findings'][1]['duplicate_proposals'][0]['duplicate_of'],'alice/F1')

    def test_duplicate_ids_unknown_references_and_json_keys_are_rejected(self):
        a=self.save(self.report());b=self.reviews/'duplicate.sdd-review.json';b.write_bytes(a.read_bytes())
        self.check(a,b,expected=2)
        unknown=self.save(self.followup('unknown','RECHECK_PASS'))
        self.check(unknown,expected=2)
        b.write_text('{"kind":"sdd-review-report","kind":"other"}')
        self.check(b,expected=2)
        invalid=self.report('bad');invalid['findings'].append(copy.deepcopy(invalid['findings'][0]))
        self.check(self.save(invalid),expected=2)

    def test_submitted_scope_and_fields_cannot_silently_expand_or_misspell(self):
        value=self.report();value['findings'][0]['scope']=['tools/missing.py'];self.check(self.save(value),expected=2)
        value=self.report();value['approved']=True;self.check(self.save(value),expected=2)
        value=self.draft();value['status']='SUBMITTED';self.check(self.save(value),expected=2)

    def test_malformed_json_shapes_have_explained_failures(self):
        report=self.report();p=self.save(report)
        for invalid in ([],None,dict(report,reviewer=None),dict(report,findings={}),dict(report,environment=[])):
            with self.subTest(invalid=invalid):
                p.write_text(json.dumps(invalid));self.check(p,expected=2)
        p.write_text('['*1200+'0'+']'*1200);self.check(p,expected=2)

    def test_nonregular_evidence_is_rejected_without_opening_it(self):
        directory=self.reviews/'evidence/directory';directory.mkdir()
        self.cli('evidence','--root',str(self.reviews),'--path','evidence/directory',expected=2)
        if hasattr(os,'mkfifo'):
            os.mkfifo(self.reviews/'evidence/pipe')
            # The inventory intentionally avoids reading the FIFO as test data.
            r=subprocess.run([sys.executable,str(self.source/'tools/review.py'),'evidence','--root',str(self.reviews),
                              '--path','evidence/pipe'],capture_output=True,text=True,timeout=5)
            self.assertEqual(r.returncode,2);self.assertEqual(json.loads(r.stdout)['validation'],'INVALID')

    def test_actual_review_runtime_data_is_rejected_from_package_inputs(self):
        for name,body in [('docs/private.sdd-review.json',{}),('tools/renamed.json',{'kind':'sdd-review-report'}),
                          ('docs/candidate.json',{'kind':'sdd-review-candidate'}),
                          ('docs/renamed.txt',{'kind':'sdd-review-report'})]:
            p=self.source/name;p.write_text(json.dumps(body))
            with self.subTest(name=name),self.assertRaises(ValueError):package.check(self.source)
            p.unlink()
        p=self.source/'tools/other-extension.bin';p.write_bytes(json.dumps({'kind':'sdd-review-report'}).encode('utf-16'))
        with self.assertRaises(ValueError):package.check(self.source)
