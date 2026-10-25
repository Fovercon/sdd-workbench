"""Read-only installation observations and explicit evidence limits."""
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
import doctor
import package
from install import Installation, target_directories


def inventory(root):
    result={}
    if not root.exists():return result
    for path in sorted(root.rglob('*')):
        name=str(path.relative_to(root))
        if path.is_symlink():result[name]=('link',os.readlink(path))
        elif path.is_file():result[name]=('file',path.read_bytes(),path.stat().st_mtime_ns)
        else:result[name]=('directory',)
    return result


class DoctorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name).resolve();self.home=self.base/'home'
        self.source=self.base/'source'
        for name,data in package.bundle_files(ROOT).items():
            p=self.source/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)

    def dest(self,agent='codex'):
        return target_directories([agent],self.home)[agent]

    def copy(self,dest):
        dest.mkdir(parents=True,exist_ok=True)
        for name in package.load(ROOT/'suite.json')['skills']:
            shutil.copytree(ROOT/'skills'/name,dest/name)

    def report(self,*agents,**kwargs):
        before=inventory(self.base)
        value=doctor.diagnose(list(agents) or ['codex'],home=self.home,which=lambda _name:None,**kwargs)
        self.assertEqual(inventory(self.base),before,'diagnosis mutated inputs/state')
        return value

    def codes(self,value):return {item['code'] for item in value['issues']}

    def test_missing_profiles_do_not_create_home_or_report_operational_success(self):
        value=self.report('all')
        self.assertFalse(self.home.exists())
        self.assertEqual(set(value['agents']),{'codex','hermes','zcode','deepseek','opencode','pi'})
        self.assertIn('NO_VISIBLE_DEFAULT_SKILLS',self.codes(value))
        self.assertTrue(all(a['client']['discovery']=='NOT_TESTED' for a in value['agents'].values()))

    def test_clean_managed_install_remains_unverified_at_client_boundary(self):
        Installation(self.dest()).install(ROOT)
        value=self.report('codex');self.assertEqual(value['issues'],[])
        self.assertEqual(value['agents']['codex']['found_skills'],12)
        self.assertFalse(value['environment']['executables_ran'])
        self.assertEqual(value['agents']['codex']['client']['execution'],'NOT_TESTED')

    def test_managed_edit_is_preserved_and_reported(self):
        Installation(self.dest()).install(ROOT)
        file=self.dest()/'sdd-code-review/SKILL.md';file.write_text(file.read_text()+'\nPersonal edit\n')
        value=self.report('codex')
        self.assertIn('MANAGED_CONTENT_CHANGED',self.codes(value))
        self.assertIn('CONTENT_DIFFERS_FROM_SOURCE',self.codes(value))
        self.assertIn('Personal edit',file.read_text())

    def test_pending_transaction_and_foreign_receipt_are_not_ignored(self):
        install=Installation(self.dest());install.install(ROOT)
        install.journal_path.write_text('{}')
        value=self.report('codex');self.assertIn('PENDING_RECOVERY',self.codes(value))
        receipt=json.loads(install.receipt_path.read_text());receipt['destination']=str(self.base/'elsewhere')
        install.receipt_path.write_text(json.dumps(receipt))
        codes=self.codes(self.report('codex'))
        self.assertIn('INVALID_OR_UNREADABLE_RECEIPT',codes)
        self.assertIn('PENDING_RECOVERY',codes)

    def test_receipt_corruption_does_not_hide_readable_copies(self):
        self.copy(self.dest());state=self.dest().parent/'.sdd-workbench';state.mkdir()
        for content in ('not-json','[]','null','{"schema":1,"skills":[]}'):
            with self.subTest(content=content):
                (state/'receipt.json').write_text(content)
                value=self.report('codex')
                self.assertEqual(value['agents']['codex']['found_skills'],12)
                self.assertIn('INVALID_OR_UNREADABLE_RECEIPT',self.codes(value))

    def test_shared_discovery_is_not_assumed_for_hermes_or_zcode(self):
        self.copy(self.dest('shared'));value=self.report('all')
        for agent in ('codex','deepseek','opencode','pi'):
            self.assertEqual(value['agents'][agent]['found_skills'],12)
        for agent in ('hermes','zcode'):
            self.assertEqual(value['agents'][agent]['found_skills'],0)
            self.assertFalse(value['agents'][agent]['reads_shared_by_default'])
        self.assertTrue(all(root['receipt_version'] is None for root in value['roots']))

    def test_equal_copies_and_conflicting_copies_are_distinguished(self):
        self.copy(self.dest());self.copy(self.dest('shared'))
        value=self.report('codex')
        self.assertIn('DUPLICATE_PHYSICAL_COPIES',self.codes(value))
        self.assertNotIn('CONFLICTING_COPIES',self.codes(value))
        file=self.dest('shared')/'sdd-code-review/SKILL.md';file.write_text(file.read_text()+'\nVariant\n')
        value=self.report('codex')
        self.assertIn('CONFLICTING_COPIES',self.codes(value))
        self.assertEqual(value['agents']['codex']['conflicting'],['sdd-code-review'])

    @unittest.skipIf(sys.platform=='win32','Directory symlinks may require Windows privileges')
    def test_directory_aliases_share_identity_instead_of_duplicate_warning(self):
        shared=self.dest('shared');self.copy(shared);native=self.dest();native.mkdir(parents=True)
        for name in package.load(ROOT/'suite.json')['skills']:(native/name).symlink_to(shared/name,target_is_directory=True)
        value=self.report('codex');self.assertEqual(value['issues'],[])
        self.assertEqual(value['agents']['codex']['duplicates'],[])

    @unittest.skipIf(sys.platform=='win32','Symlinks may require Windows privileges')
    def test_broken_or_wrong_named_links_and_nested_links_are_explicit(self):
        self.copy(self.dest())
        linked=self.dest()/'sdd-plan-slices';shutil.rmtree(linked);linked.symlink_to(self.base/'missing',target_is_directory=True)
        self.assertIn('BROKEN_SKILL_LINK',self.codes(self.report('codex')))
        linked.unlink();linked.symlink_to(self.dest()/'sdd-code-review',target_is_directory=True)
        value=self.report('codex');self.assertIn('UNREADABLE_OR_INVALID_SKILL',self.codes(value))
        self.assertEqual(value['agents']['codex']['found_skills'],11)
        linked.unlink();shutil.copytree(ROOT/'skills/sdd-plan-slices',linked)
        outside=self.base/'outside';outside.write_text('not skill data')
        (linked/'external').symlink_to(outside)
        self.assertIn('UNREADABLE_OR_INVALID_SKILL',self.codes(self.report('codex')))

    @unittest.skipIf(sys.platform=='win32','Symlinks may require Windows privileges')
    def test_broken_receipt_link_cannot_be_treated_as_unmanaged_clean_install(self):
        self.copy(self.dest());state=self.dest().parent/'.sdd-workbench';state.mkdir()
        (state/'receipt.json').symlink_to(self.base/'missing-receipt')
        value=self.report('codex');self.assertIn('INVALID_OR_UNREADABLE_RECEIPT',self.codes(value))

    def test_explicit_destination_limits_scan_and_custom_state_is_supported(self):
        dest=self.base/'plugin-cache/skills';state=self.base/'custom-state'
        Installation(dest,state).install(ROOT)
        value=self.report('codex',destination=dest,state=state)
        self.assertEqual(value['issues'],[])
        self.assertEqual([root['path'] for root in value['roots']],[str(dest)])
        self.assertEqual(value['roots'][0]['state_path'],str(state))
        with self.assertRaises(ValueError):self.report('all',destination=dest)
        with self.assertRaises(ValueError):self.report('codex',state=state)

    def test_other_declared_version_is_not_labeled_corrupt(self):
        package.bump_version('0.2.0',self.source)
        Installation(self.dest()).install(self.source)
        value=self.report('codex')
        self.assertIn('VERSION_DIFFERS_FROM_SOURCE',self.codes(value))
        self.assertNotIn('MANAGED_CONTENT_CHANGED',self.codes(value))

    def test_unmanaged_content_match_does_not_fabricate_a_receipt_version(self):
        self.copy(self.dest());value=self.report('codex')
        self.assertEqual(value['issues'],[])
        item=value['roots'][0]['skills']['sdd-code-review']
        self.assertTrue(item['matches_source']);self.assertIsNone(item['receipt_version'])

    def test_cli_is_read_only_even_with_an_executable_client_on_path(self):
        self.copy(self.dest());bin_dir=self.base/'bin';bin_dir.mkdir();marker=self.base/'executed'
        # Neither a shell script nor a Windows executable stub may be run by doctor.
        client=bin_dir/('codex.cmd' if sys.platform=='win32' else 'codex')
        client.write_text('@echo ran > '+str(marker) if sys.platform=='win32' else '#!/bin/sh\necho ran > '+str(marker)+'\n')
        client.chmod(0o755)
        before=inventory(self.base);env=dict(os.environ);env['PATH']=str(bin_dir)
        result=subprocess.run([sys.executable,'-B',str(ROOT/'tools/doctor.py'),'--agent','codex','--home',str(self.home),'--json'],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        value=json.loads(result.stdout)
        self.assertEqual(value['agents']['codex']['client']['status'],'PATH_FOUND_NOT_EXECUTED')
        self.assertFalse(marker.exists());self.assertEqual(inventory(self.base),before)

    def test_cli_missing_and_invalid_scope_have_distinct_exit_codes(self):
        command=[sys.executable,'-B',str(ROOT/'tools/doctor.py'),'--home',str(self.home),'--json']
        result=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(result.returncode,1);self.assertEqual(json.loads(result.stdout)['summary'],'NEEDS_ATTENTION')
        result=subprocess.run(command+['--agent','unknown'],capture_output=True,text=True)
        self.assertEqual(result.returncode,2);self.assertEqual(json.loads(result.stdout)['summary'],'DIAGNOSTIC_FAILED')
        self.assertFalse(self.home.exists())


if __name__=='__main__':unittest.main()
