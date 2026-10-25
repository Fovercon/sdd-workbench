"""Observable install plans and process-level operations, under temporary profiles."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import package
from install import Installation, target_directories


def inventory(root):
    result = {}
    for path in sorted(root.rglob('*')):
        key = path.relative_to(root).as_posix()
        if path.is_symlink(): result[key] = ('link', os.readlink(path))
        elif path.is_file(): result[key] = ('file', hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
        else: result[key] = ('directory', path.stat().st_mtime_ns)
    return result


CRASH_RUNNER = '''import sys,os
sys.dont_write_bytecode=True
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import install
mode,trigger=sys.argv[2],Path(sys.argv[3])
if mode=='copy':
    original=install.shutil.copytree
    def crash(source,destination,*args,**kwargs):
        if Path(destination)==trigger:
            Path(destination).mkdir()
            install.shutil.copyfile(Path(source)/'SKILL.md',Path(destination)/'SKILL.md')
            os._exit(81)
        return original(source,destination,*args,**kwargs)
    install.shutil.copytree=crash
else:
    original=Path.unlink
    def crash(path,*args,**kwargs):
        if path==trigger: os._exit(82)
        return original(path,*args,**kwargs)
    Path.unlink=crash
sys.argv=['install.py']+sys.argv[4:]
sys.exit(install.main())
'''


class InstallPreview(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name).resolve();self.source=self.base/'source';self.home=self.base/'profile'
        for name,data in package.bundle_files(ROOT).items():
            p=self.source/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        self.original=package.load(self.source/'plugin.json')['version']
        major,minor,patch=map(int,self.original.split('-')[0].split('.'))
        self.upgrade_version=f'{major}.{minor}.{patch+1}'

    def cli(self,*args):
        # Deliberately no -B: a read-only preview must not create source bytecode.
        return subprocess.run([sys.executable,str(self.source/'tools/install.py'),*args,'--home',str(self.home)],capture_output=True,text=True)

    def success(self,*args):
        result=self.cli(*args);self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        return json.loads(result.stdout)

    def preview(self,*args,exit_code=0):
        before=inventory(self.base)
        result=self.cli('install','--dry-run',*args)
        self.assertEqual(inventory(self.base),before,'preview wrote files/directories/locks/caches')
        self.assertEqual(result.returncode,exit_code,result.stdout+result.stderr)
        return json.loads(result.stdout)

    def installation(self,agent='codex'):
        return Installation(target_directories([agent],self.home)[agent])

    def upgrade(self,modify=True):
        package.bump_version(self.upgrade_version,self.source)
        if modify:
            p=self.source/'skills/sdd-code-review/SKILL.md';p.write_text(p.read_text()+'\nSynthetic upgrade.\n')

    def test_fresh_preview_covers_six_targets_without_creating_profile(self):
        result=self.preview('--agent','all')
        self.assertTrue(result['read_only']);self.assertTrue(result['eligible'])
        self.assertEqual(len(result['agents']),6);self.assertFalse(self.home.exists())
        expected=package.digest(json.dumps({n:package.digest(d) for n,d in package.bundle_files(self.source).items()},sort_keys=True).encode())
        self.assertEqual(result['source']['package_sha256'],expected)
        for record in result['agents'].values():
            self.assertEqual(len(record['skills']),12)
            self.assertEqual({s['action'] for s in record['skills']},{'INSTALL'})
            self.assertTrue(all('SKILL.md' in s['files']['added'] for s in record['skills']))

    def test_repeat_is_noop_but_metadata_only_upgrade_reinstalls(self):
        self.success('install','--agent','codex')
        same=self.preview()['agents']['codex']
        self.assertFalse(same['requires_transaction'])
        self.assertEqual({s['action'] for s in same['skills']},{'UNCHANGED'})
        self.upgrade(modify=False)
        upgrade=self.preview()['agents']['codex']
        self.assertTrue(upgrade['requires_transaction'])
        self.assertEqual({s['action'] for s in upgrade['skills']},{'REINSTALL'})
        self.assertTrue(all(not any(s['files'].values()) for s in upgrade['skills']))
        self.success('install')
        self.assertEqual(self.installation().status()['version'],self.upgrade_version)

    def test_preview_reports_all_blockers_and_force_adopt_do_not_apply(self):
        self.success('install','--agent','codex')
        file=self.installation().dest/'sdd-code-review/SKILL.md';file.write_text(file.read_text()+'\nUser edit\n')
        other=self.installation('hermes').dest/'sdd-plan-slices/SKILL.md'
        other.parent.mkdir(parents=True);other.write_text('Unmanaged user work')
        self.upgrade()
        result=self.preview('--agent','all',exit_code=1)
        self.assertFalse(result['eligible']);self.assertFalse(result['agents']['codex']['eligible'])
        self.assertFalse(result['agents']['hermes']['eligible']);self.assertTrue(result['agents']['pi']['eligible'])
        forced=self.preview('--agent','all','--force','--adopt')
        item=next(s for s in forced['agents']['codex']['skills'] if s['name']=='sdd-code-review')
        self.assertTrue(item['locally_modified']);self.assertEqual(item['files']['changed'],['SKILL.md'])
        self.assertEqual(next(s for s in forced['agents']['hermes']['skills'] if s['name']=='sdd-plan-slices')['action'],'ADOPT')
        self.assertIn('User edit',file.read_text());self.assertEqual(other.read_text(),'Unmanaged user work')

    def test_removed_owned_skill_is_listed_unmanaged_others_not_scanned(self):
        self.success('install')
        unmanaged=self.installation().dest/'my-skill/SKILL.md';unmanaged.parent.mkdir();unmanaged.write_text('Mine')
        self.upgrade()
        suite=package.load(self.source/'suite.json');suite['skills'].remove('sdd-retrospective')
        (self.source/'suite.json').write_text(json.dumps(suite));shutil.rmtree(self.source/'skills/sdd-retrospective')
        result=self.preview()['agents']['codex']
        removed=next(s for s in result['skills'] if s['name']=='sdd-retrospective')
        self.assertEqual(removed['action'],'REMOVE');self.assertIn('SKILL.md',removed['files']['removed'])
        self.assertNotIn('my-skill',{s['name'] for s in result['skills']})
        self.success('install');self.assertFalse((self.installation().dest/'sdd-retrospective').exists())
        self.assertEqual(unmanaged.read_text(),'Mine')

    def test_explicit_destination_and_custom_state_match_real_execution(self):
        dest=self.base/'custom/skills';state=self.base/'state'
        options=('--agent','dsh','--dest',str(dest),'--state',str(state))
        result=self.preview(*options)['agents']['deepseek']
        self.assertEqual(result['destination'],str(dest));self.assertEqual(result['state'],str(state))
        self.success('install',*options)
        self.assertEqual(Installation(dest,state).status()['changed'],[])
        conflict=self.cli('install','--dry-run','--agent','all','--dest',str(dest))
        self.assertEqual(conflict.returncode,1)

    def test_identical_unmanaged_skill_is_explicitly_adopted_and_backed_up(self):
        install=self.installation();name='sdd-code-review'
        shutil.copytree(self.source/'skills'/name,install.dest/name)
        old=package.tree_hashes(install.dest/name)
        result=self.preview()['agents']['codex']
        row=next(s for s in result['skills'] if s['name']==name)
        self.assertEqual(row['action'],'ADOPT_IDENTICAL');self.assertFalse(row['managed_before'])
        self.assertFalse(any(row['files'].values()))
        applied=self.success('install')
        self.assertEqual(package.tree_hashes(Path(applied['backup'])/'before'/name),old)
        self.assertIn(name,install.receipt()['skills'])

    @unittest.skipIf(sys.platform=='win32','Symlink creation may require privileges')
    def test_linked_skill_is_unreadable_for_python_ownership_and_not_followed(self):
        install=self.installation();outside=self.base/'outside';outside.mkdir()
        (outside/'SKILL.md').write_text('External user content')
        install.dest.mkdir(parents=True);(install.dest/'sdd-code-review').symlink_to(outside,target_is_directory=True)
        result=self.preview('--agent','all','--adopt',exit_code=1)
        row=next(s for s in result['agents']['codex']['skills'] if s['name']=='sdd-code-review')
        self.assertEqual(row['action'],'UNREADABLE');self.assertIsNone(row['files'])
        self.assertTrue(result['agents']['hermes']['eligible'])
        self.assertEqual((outside/'SKILL.md').read_text(),'External user content')

    def test_preview_does_not_bypass_later_edits_or_same_version_drift(self):
        self.success('install');self.upgrade();self.preview()
        file=self.installation().dest/'sdd-code-review/SKILL.md';file.write_text(file.read_text()+'\nLater edit\n')
        result=self.cli('install');self.assertEqual(result.returncode,1)
        self.assertIn('Later edit',file.read_text())
        # Source metadata alone cannot make different bytes a new instance of v1.
        package.bump_version(self.original,self.source)
        result=self.preview('--force',exit_code=1)
        self.assertIn('different contents',result['agents']['codex']['blocked_reason'])

    def test_malformed_receipts_fail_without_tracebacks_or_destination_changes(self):
        install=self.installation();install.state.mkdir(parents=True)
        malformed=('[]','null','{}',json.dumps({'schema':1,'destination':str(install.dest),'skills':{},'transaction_id':'abc','version':'0.2.1','name':'other-suite'}))
        valid={'schema':1,'destination':str(install.dest),'skills':{},'transaction_id':'abc','version':'0.2.1','name':'sdd-workbench'}
        malformed += tuple(json.dumps(dict(valid,**change)) for change in (
            {'version':None},{'version':'not-a-version'},
            {'skills':{'sdd-code-review':None}},
            {'skills':{'sdd-code-review':{'SKILL.md':'bad-hash'}}}))
        for raw in malformed:
            with self.subTest(raw=raw):
                install.receipt_path.write_text(raw)
                for command in ('status','install'):
                    result=self.cli(command)
                    self.assertEqual(result.returncode,1,result.stdout+result.stderr)
                    self.assertNotIn('Traceback',result.stderr)
                    self.assertFalse(install.dest.exists())
                self.assertEqual(install.receipt_path.read_text(),raw)
        self.preview(exit_code=1)

    @unittest.skipIf(sys.platform=='win32','Symlink creation may require privileges')
    def test_dangling_receipt_and_pending_links_block_writes_and_remain_intact(self):
        install=self.installation();install.state.mkdir(parents=True)
        install.receipt_path.symlink_to(self.base/'missing-receipt')
        result=self.cli('install');self.assertEqual(result.returncode,1)
        self.assertTrue(install.receipt_path.is_symlink());self.assertFalse(install.dest.exists())
        self.preview(exit_code=1);install.receipt_path.unlink()
        install.journal_path.symlink_to(self.base/'missing-journal')
        self.assertTrue(self.success('status')['pending_recovery'])
        self.preview(exit_code=1)
        self.assertEqual(self.cli('install').returncode,1)
        self.assertEqual(self.cli('recover').returncode,1)
        self.assertTrue(install.journal_path.is_symlink());self.assertFalse(install.dest.exists())

    def test_corrupt_journal_json_is_explained_and_retained(self):
        install=self.installation();install.state.mkdir(parents=True)
        for raw in ('[]','null','{}'):
            with self.subTest(raw=raw):
                install.journal_path.write_text(raw)
                result=self.cli('recover');self.assertEqual(result.returncode,1)
                self.assertNotIn('Traceback',result.stderr)
                self.assertEqual(install.journal_path.read_text(),raw)
                self.preview(exit_code=1)

    def crash(self,mode,trigger,*args):
        harness=self.base/'crash_runner.py';harness.write_text(CRASH_RUNNER)
        return subprocess.run([sys.executable,'-B',str(harness),str(self.source/'tools'),mode,str(trigger),*args,'--home',str(self.home)],capture_output=True,text=True)

    def test_real_process_crash_partial_multi_upgrade_recovers_then_finishes(self):
        self.success('install','--agent','all');self.upgrade()
        hermes=self.installation('hermes')
        user=hermes.dest/'my-skill/SKILL.md';user.parent.mkdir();user.write_text('User-owned outside suite')
        result=self.crash('copy',hermes.dest/'sdd-context-handoff','install','--agent','all')
        self.assertEqual(result.returncode,81)
        states=self.success('status','--agent','all')['agents']
        self.assertEqual(states['codex']['version'],self.upgrade_version);self.assertTrue(states['hermes']['pending_recovery'])
        preview=self.preview('--agent','all',exit_code=1)
        self.assertFalse(preview['agents']['hermes']['eligible']);self.assertTrue(preview['agents']['codex']['eligible'])
        recovery=self.success('recover','--agent','hermes')['agents']['hermes']
        self.assertTrue(recovery['recovered']);self.assertFalse(recovery['committed'])
        self.assertEqual(hermes.status()['version'],self.original)
        self.success('install','--agent','all')
        for dest in target_directories(['all'],self.home).values():
            self.assertEqual(Installation(dest).status()['version'],self.upgrade_version);self.assertEqual(Installation(dest).status()['changed'],[])
        self.assertEqual(user.read_text(),'User-owned outside suite')

    def test_real_process_crash_after_receipt_commit_keeps_completed_version(self):
        self.success('install');self.upgrade()
        install=self.installation()
        result=self.crash('commit',install.journal_path,'install')
        self.assertEqual(result.returncode,82)
        recovery=self.success('recover')
        self.assertTrue(recovery['committed']);self.assertEqual(install.status()['version'],self.upgrade_version)
        self.assertFalse(install.journal_path.exists());self.assertEqual(install.status()['changed'],[])

    def test_new_edit_after_process_crash_is_not_discarded_by_recovery(self):
        self.success('install');self.upgrade();install=self.installation()
        self.assertEqual(self.crash('copy',install.dest/'sdd-context-handoff','install').returncode,81)
        note=install.dest/'sdd-context-handoff/user-note.txt';note.write_text('New work after crash')
        result=self.cli('recover');self.assertEqual(result.returncode,1)
        self.assertEqual(note.read_text(),'New work after crash');self.assertTrue(install.journal_path.exists())
        # Fixture owner explicitly saves and removes only this known synthetic edit.
        saved=self.base/'saved-user-note.txt';shutil.copy2(note,saved);note.unlink()
        self.success('recover');self.assertEqual(saved.read_text(),'New work after crash')
        self.assertEqual(install.status()['version'],self.original)

    def test_force_upgrade_backup_and_cli_rollback_preserve_original_user_edit(self):
        self.success('install','--agent','all');install=self.installation()
        file=install.dest/'sdd-code-review/SKILL.md';file.write_text(file.read_text()+'\nRetain this local edit\n');original=file.read_bytes()
        self.upgrade();self.preview('--agent','all',exit_code=1)
        before=inventory(self.home);self.assertEqual(self.cli('install','--agent','all').returncode,1)
        self.assertEqual(inventory(self.home),before)
        self.preview('--agent','all','--force')
        result=self.success('install','--agent','all','--force')['agents']['codex']
        self.assertEqual((Path(result['backup'])/'before/sdd-code-review/SKILL.md').read_bytes(),original)
        self.success('rollback','--agent','all');self.assertEqual(file.read_bytes(),original)
        # The old receipt never claimed ownership of the user's edit bytes.
        self.assertIn('sdd-code-review',install.status()['changed'])

    def test_corrupt_rollback_record_cannot_crash_or_escape_owned_directories(self):
        self.success('install');self.upgrade();applied=self.success('install')
        journal=Path(applied['backup'])/'transaction.json';original=json.loads(journal.read_text())
        outside=self.home/'.codex/outside';outside.mkdir();(outside/'marker.txt').write_text('Unmanaged data')
        malicious=dict(original,before_hashes={'../outside':None},after_hashes={'../outside':None})
        for invalid in ([],None,dict(original,before_hashes=None),malicious):
            with self.subTest(invalid=invalid):
                journal.write_text(json.dumps(invalid));before=inventory(self.base)
                result=self.cli('rollback');self.assertEqual(result.returncode,1)
                self.assertNotIn('Traceback',result.stderr)
                self.assertEqual(inventory(self.base),before)
                self.assertEqual((outside/'marker.txt').read_text(),'Unmanaged data')
        journal.write_text(json.dumps(original));self.success('rollback')
        self.assertEqual(self.installation().status()['version'],self.original)
