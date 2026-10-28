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

    def test_plain_python_query_does_not_write_import_caches_outside_project(self):
        # -B in other tests must not hide writes to a read-only supplied runtime.
        runtime = self.root / 'runtime'
        shutil.copytree(CLI.parent, runtime, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo'))
        self.input.write_text(json.dumps(self.data, ensure_ascii=False), encoding='utf-8')
        before = {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()}
        env = {k: v for k, v in os.environ.items() if k not in ('PYTHONDONTWRITEBYTECODE', 'PYTHONPYCACHEPREFIX')}
        run = subprocess.run([sys.executable, str(runtime / 'project_view.py'), 'trace', '--root', str(self.root),
                              '--input', str(self.input), '--changed-id', 'R1'], capture_output=True, text=True, env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(before, {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
