"""Release identity, real archive contents and safe whole-suite installation."""
import copy
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import package
from install import Installation, atomic_json


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.source = self.root / 'source'
        # Always evaluate an isolated copy; never mutate the developer's installed skills.
        for name, data in package.bundle_files(ROOT).items():
            path = self.source / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        self.current_version = package.load(self.source / 'plugin.json')['version']
        major, minor, patch_version = map(int, self.current_version.split('-')[0].split('.'))
        self.upgrade_version = f'{major}.{minor}.{patch_version + 1}'
        self.dest = self.root / 'codex' / 'skills'
        self.installation = Installation(self.dest)

    def version(self, value):
        package.bump_version(value, self.source)

    def installed(self, name='sdd-workflow-router'):
        return self.dest / name / 'SKILL.md'

    def test_catalog_and_compatibility_are_one_release(self):
        plugin, suite, files = package.check(self.source)
        self.assertEqual(plugin['version'], self.current_version)
        self.assertEqual(len(suite['skills']), 12)
        self.assertIn('skills/sdd-workflow-router/scripts/feedback_server.py', files)
        self.assertIn('skills/sdd-workflow-router/scripts/project_view_lib/vendor/mermaid-12.2.0.min.js.gz', files)
        self.assertTrue(all('05-notes' not in name and 'PPT' not in name for name in files))

    def test_project_process_records_never_enter_a_release(self):
        for folder in ('optimization', 'releases'):
            path=self.source/'docs'/folder/'private-trial.md'
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text('Local experiment: /Users/private/work, not a reusable skill.')
        files=package.bundle_files(self.source)
        self.assertFalse(any(name.startswith(('docs/optimization/','docs/releases/')) for name in files))
        self.assertIn('CONTRIBUTING.md',files)
        self.assertIn('SECURITY.md',files)

    def test_active_installation_examples_use_the_latest_dated_release(self):
        # Development metadata may be ahead while a user explicitly withholds release.
        notes=(ROOT/'CHANGELOG.md').read_text(encoding='utf-8')
        version=re.search(r'^## \[(\d+\.\d+\.\d+)\] - \d{4}-\d{2}-\d{2}$',notes,re.M)[1]
        target=package.load(ROOT/'plugin.json')['version'].split('-')[0]
        self.assertLessEqual(tuple(map(int,version.split('.'))),tuple(map(int,target.split('.'))))
        for file in (ROOT/'README.md',ROOT/'docs/AGENT-COMPATIBILITY.md'):
            text=file.read_text(encoding='utf-8')
            pins=re.findall(r'sdd-workbench(?:/tree/|/releases/tag/|#|@)v(\d+\.\d+\.\d+)',text)
            pins+=re.findall(r'(?:--ref|--branch|git checkout) v(\d+\.\d+\.\d+)',text)
            self.assertTrue(pins,file)
            self.assertEqual(set(pins),{version},file)

    def test_undated_draft_notes_cannot_be_used_for_tag_publication(self):
        self.version(self.upgrade_version)
        path=self.source/'CHANGELOG.md';before=path.read_text(encoding='utf-8')
        path.write_text('# 更新记录\n\n'+f'## [{self.upgrade_version}]\n\nDraft only.\n\n'+before.partition('\n')[2],encoding='utf-8')
        with self.assertRaises(ValueError):package.release_notes(self.source)
        path.write_text('# 更新记录\n\n'+f'## [{self.upgrade_version}] - 2026-10-26\n\nReady notes.\n\n'+before.partition('\n')[2],encoding='utf-8')
        self.assertEqual(package.release_notes(self.source),'Ready notes.\n')

    def test_all_adapter_projections_and_complete_resources_are_packaged(self):
        _, _, files = package.check(self.source)
        for name in ('adapters/deepseek.mjs', 'agent-targets.json', 'cordis.patch.yml',
                     'marketplace.json', '.zcode-plugin/plugin.json', '.zcode-plugin/marketplace.json'):
            self.assertIn(name, files)
        self.version(self.upgrade_version)
        package.check(self.source)
        for name in ('plugin.json', '.codex-plugin/plugin.json', '.zcode-plugin/plugin.json',
                     'package.json', 'package-lock.json'):
            self.assertEqual(package.load(self.source / name)['version'], self.upgrade_version)

    def test_adapter_drift_and_unsafe_target_paths_are_rejected(self):
        mutations = [('.zcode-plugin/plugin.json', lambda v: v.update(version='9.0.0')),
                     ('package.json', lambda v: v.update(pi={'skills': ['./copies']})),
                     ('package.json', lambda v: v.update(dsh={'bundle': {'patch': './missing.yml'}})),
                     ('agent-targets.json', lambda v: v['targets']['zcode'].update(path='../outside')),
                     ('agent-targets.json', lambda v: v['targets']['zcode'].update(path='C:/outside')),
                     ('agent-targets.json', lambda v: v['targets']['zcode'].update(path='..\\outside')),
                     ('agent-targets.json', lambda v: v['targets']['zcode'].update(aliases=['codex'])),
                     ('agent-targets.json', lambda v: v['targets']['pi'].update(reads_shared='yes')),
                     ('agent-targets.json', lambda v: v['targets']['pi'].update(command='pi --version'))]
        for name, mutate in mutations:
            path = self.source / name; original = path.read_bytes()
            data = package.load(path); mutate(data); atomic_json(path, data)
            with self.subTest(name=name), self.assertRaises(ValueError): package.check(self.source)
            path.write_bytes(original)
        (self.source / 'cordis.patch.yml').write_text('- insert: []\n')
        with self.assertRaises(ValueError): package.check(self.source)

    def test_manifest_drift_missing_skill_and_symlink_are_rejected(self):
        path = self.source / '.codex-plugin/plugin.json'; old = path.read_bytes()
        data = package.load(path); data['version'] = '9.0.0'; atomic_json(path, data)
        with self.assertRaises(ValueError): package.check(self.source)
        path.write_bytes(old)
        shutil.rmtree(self.source / 'skills/sdd-retrospective')
        with self.assertRaises(ValueError): package.check(self.source)

    def test_bundle_is_reproducible_verifiable_and_installable_from_zip(self):
        a = package.build(self.source, self.root / 'a'); b = package.build(self.source, self.root / 'b')
        self.assertEqual(a.read_bytes(), b.read_bytes())
        manifest = package.verify(a)
        self.assertEqual(len(manifest['skills']), 12)
        with ZipFile(a) as archive: archive.extractall(self.root / 'unpacked')
        unpacked = self.root / 'unpacked/sdd-workbench'
        package.check(unpacked)
        result = self.installation.install(unpacked)
        self.assertEqual(result['skills'], 12)
        self.assertEqual(self.installation.status()['changed'], [])
        script = unpacked / 'tools/install.py'; script.write_text('modified', encoding='utf-8')
        with self.assertRaises(ValueError): package.check(unpacked)

    def test_archive_tampering_and_private_state_are_detected(self):
        a = package.build(self.source, self.root / 'a')
        with self.assertWarns(UserWarning):
            with ZipFile(a, 'a') as archive: archive.writestr('sdd-workbench/README.md', b'changed')
        with self.assertRaises(ValueError): package.verify(a)
        (self.source / 'skills/sdd-workflow-router/user.sqlite3').write_bytes(b'private state')
        with self.assertRaises(ValueError): package.check(self.source)

    def test_initial_install_and_repeat_leave_unrelated_skills_alone(self):
        other = self.dest / 'unrelated' / 'SKILL.md'; other.parent.mkdir(parents=True); other.write_text('owned by user')
        result = self.installation.install(self.source)
        self.assertEqual(result['version'], self.current_version)
        self.assertEqual(self.installation.status()['changed'], [])
        self.assertEqual(len(self.installation.receipt()['skills']), 12)
        repeat = self.installation.install(self.source)
        self.assertTrue(repeat['unchanged'])
        self.assertEqual(len(list((self.installation.state / 'transactions').iterdir())), 1)
        self.assertEqual(other.read_text(), 'owned by user')

    def test_upgrade_and_rollback_restore_exact_prior_content(self):
        self.installation.install(self.source)
        before = self.installed().read_bytes()
        self.version(self.upgrade_version)
        with (self.source / 'skills/sdd-workflow-router/SKILL.md').open('a') as stream: stream.write('\nNew version note.\n')
        self.installation.install(self.source)
        self.assertNotEqual(self.installed().read_bytes(), before)
        self.assertEqual(self.installation.status()['version'], self.upgrade_version)
        self.installation.rollback()
        self.assertEqual(self.installation.status()['version'], self.current_version)
        self.assertEqual(self.installed().read_bytes(), before)
        self.assertEqual(self.installation.status()['changed'], [])

    def test_unmanaged_conflict_requires_adoption_and_rollback_restores_it(self):
        self.installed().parent.mkdir(parents=True); self.installed().write_text('legacy personal edits')
        with self.assertRaises(ValueError): self.installation.install(self.source)
        self.assertEqual(self.installed().read_text(), 'legacy personal edits')
        result = self.installation.install(self.source, adopt=True)
        backup = Path(result['backup']) / 'before/sdd-workflow-router/SKILL.md'
        self.assertEqual(backup.read_text(), 'legacy personal edits')
        self.installation.rollback()
        self.assertFalse(self.installation.status()['installed'])
        self.assertEqual(self.installed().read_text(), 'legacy personal edits')
        self.assertFalse((self.dest / 'sdd-plan-slices').exists())

    def test_local_edit_blocks_upgrade_and_force_still_backs_it_up(self):
        self.installation.install(self.source)
        self.installed().write_text('my custom rule')
        self.version(self.upgrade_version)
        with self.assertRaises(ValueError): self.installation.install(self.source)
        result = self.installation.install(self.source, force=True)
        self.assertEqual((Path(result['backup']) / 'before/sdd-workflow-router/SKILL.md').read_text(), 'my custom rule')
        self.installation.rollback()
        self.assertEqual(self.installed().read_text(), 'my custom rule')
        self.assertIn('sdd-workflow-router', self.installation.status()['changed'])

    def test_reusing_version_for_changed_release_is_rejected(self):
        self.installation.install(self.source)
        with (self.source / 'skills/sdd-workflow-router/SKILL.md').open('a') as stream: stream.write('\ndifferent contents\n')
        with self.assertRaises(ValueError): self.installation.install(self.source)
        self.assertEqual(self.installation.status()['changed'], [])

    def test_removed_managed_skill_is_restored_by_rollback(self):
        self.installation.install(self.source)
        self.version(self.upgrade_version)
        data = package.load(self.source / 'suite.json'); data['skills'].remove('sdd-retrospective'); atomic_json(self.source / 'suite.json', data)
        shutil.rmtree(self.source / 'skills/sdd-retrospective')
        self.installation.install(self.source)
        self.assertFalse((self.dest / 'sdd-retrospective').exists())
        self.installation.rollback()
        self.assertTrue((self.dest / 'sdd-retrospective/SKILL.md').is_file())

    def interrupted(self):
        self.installation.install(self.source)
        self.version(self.upgrade_version)
        original = shutil.copytree
        def fail(source, destination, *args, **kwargs):
            if Path(destination) == self.dest / 'sdd-context-handoff':
                Path(destination).mkdir()
                # Simulate interruption after copying a valid subset of the new tree.
                shutil.copyfile(Path(source) / 'SKILL.md', Path(destination) / 'SKILL.md')
                raise OSError('simulated interruption')
            return original(source, destination, *args, **kwargs)
        with patch('install.shutil.copytree', side_effect=fail):
            with self.assertRaises(OSError): self.installation.install(self.source)
        self.assertTrue(self.installation.status()['pending_recovery'])

    def test_interrupted_install_blocks_writes_and_recovers_partial_copy(self):
        self.interrupted()
        with self.assertRaises(ValueError): self.installation.install(self.source)
        restarted = Installation(self.dest)
        self.assertTrue(restarted.recover()['recovered'])
        self.assertFalse(restarted.status()['pending_recovery'])
        self.assertEqual(restarted.status()['version'], self.current_version)
        self.assertEqual(restarted.status()['changed'], [])

    def test_recovery_preserves_unknown_edits_after_interruption(self):
        self.interrupted()
        unexpected = self.dest / 'sdd-context-handoff/new-work.md'; unexpected.write_text('new work after crash')
        with self.assertRaises(ValueError): self.installation.recover()
        self.assertEqual(unexpected.read_text(), 'new work after crash')
        unexpected.unlink()
        self.installation.recover()

    def test_crash_after_receipt_commit_preserves_completed_upgrade(self):
        self.installation.install(self.source); self.version(self.upgrade_version)
        original = Path.unlink
        def interrupt(path, *args, **kwargs):
            if path == self.installation.journal_path: raise OSError('crash after commit')
            return original(path, *args, **kwargs)
        with patch('pathlib.Path.unlink', new=interrupt):
            with self.assertRaises(OSError): self.installation.install(self.source)
        self.assertTrue(self.installation.recover()['committed'])
        self.assertEqual(self.installation.status()['version'], self.upgrade_version)

    def test_tampered_backup_and_wrong_state_destination_are_rejected(self):
        self.installation.install(self.source); self.version(self.upgrade_version)
        result = self.installation.install(self.source)
        backup = Path(result['backup']) / 'before/sdd-workflow-router/SKILL.md'; backup.write_text('tampered')
        with self.assertRaises(ValueError): self.installation.rollback()
        other = Installation(self.root / 'other-skills', self.installation.state)
        with self.assertRaises(ValueError): other.install(self.source)
        self.assertEqual(self.installation.status()['version'], self.upgrade_version)

    def test_install_lock_rejects_parallel_writes(self):
        other = Installation(self.dest)
        with self.installation.locked():
            with self.assertRaises(ValueError): other.install(self.source)

    def test_status_is_read_only_and_overlapping_state_is_rejected(self):
        self.assertFalse(self.installation.status()['installed'])
        self.assertFalse(self.installation.state.exists())
        with self.assertRaises(ValueError): Installation(self.dest, self.dest / 'state')
        with self.assertRaises((ValueError, OSError)): self.installation.install(self.source / 'skills')

    @unittest.skipIf(sys.platform == 'win32', 'Symlink creation may require Windows privileges')
    def test_symlinked_skill_never_redirects_installer_writes(self):
        outside = self.root / 'outside'; outside.mkdir(); (outside / 'SKILL.md').write_text('do not touch')
        self.dest.mkdir(parents=True); (self.dest / 'sdd-workflow-router').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError): self.installation.install(self.source, adopt=True)
        self.assertEqual((outside / 'SKILL.md').read_text(), 'do not touch')


if __name__ == '__main__':
    unittest.main()
