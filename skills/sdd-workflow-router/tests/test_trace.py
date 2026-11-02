"""Declared dependencies are navigation, not semantic validity or approval."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from project_view_lib.evidence import source_path

from workstream_fixture import fixture

CLI = Path(__file__).resolve().parents[1] / 'scripts/project_view.py'


class TraceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = fixture(self.root)
        self.input = self.root / 'observations.json'

    def run_cli(self, *extra, seeds=('R1',)):
        self.input.write_text(json.dumps(self.data, ensure_ascii=False), encoding='utf-8')
        args = [sys.executable, '-B', str(CLI), 'trace', '--root', str(self.root), '--input', str(self.input)]
        for key in seeds:
            args += ['--changed-id', key]
        return subprocess.run([*args, *extra], capture_output=True, text=True)

    def test_transitive_query_preserves_current_facts_and_no_path_is_not_unchanged(self):
        run = self.run_cli()
        self.assertEqual(run.returncode, 0, run.stderr)
        report = json.loads(run.stdout)
        self.assertEqual(report['input_sha256'], hashlib.sha256(self.input.read_bytes()).hexdigest())
        rows = {r['id']: r for r in report['items']}
        self.assertEqual(rows['R1']['selection'], 'CHANGED_INPUT')
        self.assertEqual({r['id'] for r in rows.values() if r['selection'] == 'REACHED'},
                         {'S1 范围%', 'S2', 'S3', 'S4', 'V1', 'V2', 'V3'})
        self.assertEqual(rows['V2']['reached_via'], ['S2'])
        self.assertEqual(rows['V1']['recorded_result'], 'PASS')
        self.assertEqual(rows['V1']['recorded_state'], 'SATISFIED')
        self.assertTrue(all(r['freshness'] == 'CURRENT' for r in rows.values()))
        for key in ('R2', 'R3', 'code1', 'code2'):
            self.assertEqual(rows[key]['selection'], 'NO_RECORDED_PATH')
        self.assertEqual(report['coverage'], 'DECLARED_LINKS_ONLY')
        self.assertNotIn('UNCHANGED', run.stdout)

    def test_shared_code_multiseed_edges_and_navigation_have_distinct_meanings(self):
        self.data['items'] += [
            dict(id='edge', label='调用关系', state='SATISFIED', view='structure', kind='code_observation',
                 sources=self.data['items'][0]['sources'], **{'from': 'code1', 'to': 'code2'}),
            dict(id='design', label='配对导航', stage='Tasks', state='SATISFIED', view='design', kind='design',
                 sources=self.data['items'][0]['sources'], mermaid='flowchart LR\n A-->B', related_ids=['code1'])]
        run = self.run_cli(seeds=('code1', 'R3', 'code1'))
        self.assertEqual(run.returncode, 0, run.stderr)
        report = json.loads(run.stdout); rows = {r['id']: r for r in report['items']}
        self.assertEqual(report['changed_ids'], ['code1', 'R3'])
        self.assertEqual(rows['edge']['selection'], 'REACHED')
        self.assertEqual(rows['edge']['reached_via'], ['code1'])
        self.assertEqual(rows['code2']['selection'], 'NO_RECORDED_PATH')
        self.assertEqual(rows['design']['selection'], 'NO_RECORDED_PATH')
        self.assertEqual(rows['S1 范围%']['selection'], 'REACHED')
        self.assertEqual(rows['S3']['reached_via'], ['R3', 'S2'])
        self.assertEqual(rows['S4']['reached_via'], ['R3', 'S1 范围%'])

    def test_record_chain_propagates_and_query_never_writes_or_refreshes_hashes(self):
        self.data['lifecycle']['stage_items']['Finish'] = 'finish'
        ref = self.data['items'][0]['sources']
        self.data['items'] += [dict(id='finish', label='交付记录', stage='Finish', view='progress',
            kind='assessment', state='UNKNOWN', sources=ref, note='合成记录，不代表交付批准',
            stage_detail=dict(type='handoff', record_ids=['V1']))]
        self.run_cli()
        before = {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()}
        run = self.run_cli()
        self.assertEqual(run.returncode, 0, run.stderr)
        rows = {r['id']: r for r in json.loads(run.stdout)['items']}
        self.assertEqual(rows['finish']['selection'], 'REACHED')
        self.assertEqual(rows['finish']['recorded_state'], 'UNKNOWN')
        self.assertEqual(rows['finish']['reached_via'], ['V1'])
        self.assertEqual(before, {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()})

    def test_actual_file_change_and_missing_source_do_not_expand_semantic_query(self):
        r1 = next(i for i in self.data['items'] if i['id'] == 'R1')
        r3 = next(i for i in self.data['items'] if i['id'] == 'R3')
        # Same document, distinct semantic records: identity changes conservatively for both.
        r3['sources'] = r1['sources']
        (self.root / r1['sources'][0]['path']).write_text('changed', encoding='utf-8')
        missing = next(i for i in self.data['items'] if i['id'] == 'code2')
        (self.root / missing['sources'][0]['path']).unlink()
        run = self.run_cli()
        self.assertEqual(run.returncode, 2, run.stderr)
        rows = {r['id']: r for r in json.loads(run.stdout)['items']}
        self.assertEqual(rows['V1']['freshness'], 'STALE')
        self.assertEqual(rows['R3']['selection'], 'NO_RECORDED_PATH')
        self.assertEqual(rows['R3']['freshness'], 'STALE')
        self.assertEqual(rows['V2']['freshness'], 'UNKNOWN')
        self.assertEqual(rows['V1']['recorded_result'], 'PASS')
        self.assertEqual(rows['R1']['sources'][0]['sha256'], r1['sources'][0]['sha256'])

    def test_invalid_query_and_sources_fail_without_output(self):
        for seeds, extra in [((), ()), (('missing',), ()), (('R1',), ('--output', str(self.root / 'bad'))),
                              (('R1',), ('--reason', 'guess')), (('R1',), ('--summary',))]:
            with self.subTest(seeds=seeds, extra=extra):
                run = self.run_cli(*extra, seeds=seeds)
                self.assertNotEqual(run.returncode, 0)
                self.assertFalse(run.stdout.strip())
                self.assertNotIn('Traceback', run.stderr)
                self.assertFalse((self.root / 'bad').exists())
        self.data['items'][0]['sources'][0]['path'] = '../outside'
        run = self.run_cli()
        self.assertEqual(run.returncode, 1)
        self.assertIn('escapes', run.stderr)

    def test_trace_option_is_rejected_by_other_commands(self):
        for command in ('describe', 'check', 'render', 'update'):
            run = subprocess.run([sys.executable, '-B', str(CLI), command, '--changed-id', 'R1'], capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertFalse(run.stdout.strip())

    def test_source_query_selects_every_citing_record_before_traversal(self):
        run = self.run_cli('--changed-source', 'component-1.py', seeds=())
        self.assertEqual(run.returncode, 0, run.stderr)
        report = json.loads(run.stdout); rows = {r['id']: r for r in report['items']}
        self.assertEqual(report['changed_ids'], ['code1', 'S1 范围%'])
        self.assertEqual(report['changed_sources'], [{'path': 'component-1.py', 'item_ids': ['code1', 'S1 范围%']}])
        self.assertEqual(report['unmapped_sources'], [])
        self.assertEqual(rows['S1 范围%']['selected_by_sources'], ['component-1.py'])
        self.assertEqual(rows['V1']['selection'], 'REACHED')
        self.assertEqual(rows['V1']['recorded_result'], 'PASS')
        self.assertEqual(rows['R1']['selection'], 'NO_RECORDED_PATH')
        self.assertEqual(rows['R1']['selected_by_sources'], [])

    def test_source_aliases_and_ids_have_stable_union_and_legacy_shape(self):
        path = next(i for i in self.data['items'] if i['id'] == 'R1')['sources'][0]['path']
        run = self.run_cli('--changed-source', './' + path, '--changed-source', 'nested/../' + path,
                           seeds=('R3', 'R3'))
        self.assertEqual(run.returncode, 0, run.stderr)
        report = json.loads(run.stdout)
        self.assertEqual(report['changed_ids'], ['R3', 'R1'])
        self.assertEqual(report['changed_sources'], [{'path': path, 'item_ids': ['R1']}])
        self.assertNotIn('changed_sources', json.loads(self.run_cli().stdout))

    def test_unmapped_source_is_an_explicit_gap_even_when_every_path_is_unmapped(self):
        (self.root / 'unmapped.md').write_text('No observation cites this file.\n')
        run = self.run_cli('--changed-source', 'unmapped.md', '--changed-source', 'prospective.md', seeds=())
        self.assertEqual(run.returncode, 0, run.stderr)
        report = json.loads(run.stdout)
        self.assertEqual(report['changed_ids'], [])
        self.assertEqual(report['unmapped_sources'], ['unmapped.md', 'prospective.md'])
        self.assertTrue(all(not row['item_ids'] for row in report['changed_sources']))
        self.assertTrue(all(row['selection'] == 'NO_RECORDED_PATH' for row in report['items']))
        self.assertNotIn('UNCHANGED', run.stdout)
        mixed = self.run_cli('--changed-source', 'unmapped.md', seeds=('R1',))
        self.assertEqual(json.loads(mixed.stdout)['changed_ids'], ['R1'])
        self.assertEqual(json.loads(mixed.stdout)['unmapped_sources'], ['unmapped.md'])

    def test_source_selection_keeps_same_file_meaning_and_actual_stale_missing_evidence_separate(self):
        r1 = next(i for i in self.data['items'] if i['id'] == 'R1')
        r3 = next(i for i in self.data['items'] if i['id'] == 'R3')
        r3['sources'] = r1['sources']
        path = r1['sources'][0]['path']
        (self.root / path).write_text('Changed bytes do not decide the meaning of both records.\n')
        run = self.run_cli('--changed-source', path, seeds=())
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertTrue(run.stdout.strip(), run.stderr)
        report = json.loads(run.stdout); rows = {r['id']: r for r in report['items']}
        self.assertEqual(report['changed_ids'], ['R1', 'R3'])
        self.assertEqual(rows['R3']['freshness'], 'STALE')
        self.assertEqual(rows['R3']['recorded_state'], 'SATISFIED')
        self.assertEqual(rows['R1']['sources'][0]['sha256'], r1['sources'][0]['sha256'])
        (self.root / path).unlink()
        missing = self.run_cli('--changed-source', path, seeds=())
        self.assertEqual(missing.returncode, 2)
        self.assertEqual(json.loads(missing.stdout)['changed_ids'], ['R1', 'R3'])
        missing_rows = {r['id']: r for r in json.loads(missing.stdout)['items']}
        self.assertEqual(missing_rows['R1']['freshness'], 'UNKNOWN')

    def test_source_query_respects_root_boundary_and_command_scope(self):
        (self.root / 'folder').mkdir()
        outside = self.root.parent / (self.root.name + '-outside')
        (self.root / 'escape').symlink_to(outside)
        for value in ('../outside.md', str(outside), '.', 'folder', 'escape'):
            with self.subTest(value=value):
                run = self.run_cli('--changed-source', value, seeds=())
                self.assertEqual(run.returncode, 1, run.stderr)
                self.assertFalse(run.stdout.strip())
                self.assertNotIn('Traceback', run.stderr)
        for command in ('describe', 'check', 'render', 'update'):
            run = subprocess.run([sys.executable, '-B', str(CLI), command, '--changed-source', 'x.md'], capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertFalse(run.stdout.strip())

    def test_windows_unresolvable_symlink_error_is_rejected(self):
        unresolved = self.root / 'windows-loop'
        error = OSError(22, 'Cannot resolve filename')
        error.winerror = 1921
        with mock.patch.object(Path, 'resolve', return_value=unresolved), mock.patch.object(Path, 'stat', side_effect=error):
            with self.assertRaises(ValueError):
                source_path(self.root, 'windows-loop')

    def test_cyclic_source_paths_are_clean_read_only_input_errors(self):
        for name, target in [('self-loop', 'self-loop'), ('cycle-a', 'cycle-b'), ('cycle-b', 'cycle-a')]:
            (self.root / name).symlink_to(target)
        original = self.data['items'][0]['sources'][0]['path']
        for name in ('self-loop', 'cycle-a', 'self-loop/missing.md', 'cycle-a/missing.md'):
            for location in ('selector', 'observation'):
                with self.subTest(name=name, location=location):
                    self.data['items'][0]['sources'][0]['path'] = original
                    if location == 'observation':
                        self.data['items'][0]['sources'][0]['path'] = name
                    self.input.write_text(json.dumps(self.data, ensure_ascii=False), encoding='utf-8')
                    before = {p.relative_to(self.root).as_posix():
                              ('link', os.readlink(p)) if p.is_symlink() else ('file', p.read_bytes())
                              for p in self.root.rglob('*') if p.is_symlink() or p.is_file()}
                    run = self.run_cli('--changed-source', name, seeds=())
                    self.assertEqual(run.returncode, 1, run.stderr)
                    self.assertFalse(run.stdout.strip())
                    self.assertNotIn('Traceback', run.stderr)
                    self.assertTrue(run.stderr.strip())
                    self.assertEqual(before, {p.relative_to(self.root).as_posix():
                                     ('link', os.readlink(p)) if p.is_symlink() else ('file', p.read_bytes())
                                     for p in self.root.rglob('*') if p.is_symlink() or p.is_file()})
                    self.data['items'][0]['sources'][0]['path'] = original

    def test_plain_python_query_does_not_write_import_caches_outside_project(self):
        # -B in other tests must not hide writes to a read-only supplied runtime.
        runtime = self.root / 'runtime'
        shutil.copytree(CLI.parent, runtime, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo'))
        self.input.write_text(json.dumps(self.data, ensure_ascii=False), encoding='utf-8')
        before = {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()}
        env = {k: v for k, v in os.environ.items() if k not in ('PYTHONDONTWRITEBYTECODE', 'PYTHONPYCACHEPREFIX')}
        run = subprocess.run([sys.executable, str(runtime / 'project_view.py'), 'trace', '--root', str(self.root),
                              '--input', str(self.input), '--changed-source', 'component-1.py'], capture_output=True, text=True, env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(before, {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
