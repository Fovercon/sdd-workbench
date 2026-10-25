"""Regression oracles for typed coverage; a green test count is not acceptance."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from workstream_fixture import fixture

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from project_view_lib import evidence, workstream


class WorkstreamTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = fixture(self.root)

    def item(self, key):
        return next(i for i in self.data['items'] if i['id'] == key)

    def model(self):
        spec = importlib.util.spec_from_file_location('view_cli', SCRIPTS / 'project_view.py')
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        cli.validate(self.data)
        self.inspected = evidence.inspect(self.root, self.data)
        return workstream.model(self.data, self.inspected)

    def row(self, key):
        return next(r for r in self.model()['rows'] if r['item']['id'] == key)

    def run_view(self, output='v1', *args):
        p = self.root / 'input.json'
        p.write_text(json.dumps(self.data, ensure_ascii=False))
        return subprocess.run([sys.executable, '-B', str(SCRIPTS / 'project_view.py'),
            'render', '--root', str(self.root), '--input', str(p), '--output', str(self.root / output), *args], capture_output=True, text=True)

    def test_mixed_statuses_have_one_covered_requirement_and_visible_gaps(self):
        m = self.model()
        self.assertEqual([r['verdict'] for r in m['rows']], ['COVERED', 'GAP', 'GAP'])
        self.assertEqual(m['covered'], 1)
        self.assertTrue(any('未执行' in p for p in m['rows'][1]['gaps']))
        self.assertTrue(any('缺少验证记录' in p for p in m['rows'][2]['gaps']))

    def test_single_passing_check_cannot_cover_a_second_slice(self):
        extra = copy.deepcopy(self.item('S1 范围%'))
        extra.update(id='extra')
        self.data['items'].append(extra)
        row = self.row('R1')
        self.assertEqual(row['verdict'], 'GAP')
        self.assertIn('范围选择与预览：缺少验证记录', row['gaps'])

    def test_pass_needs_done_implementation_and_usable_judgments(self):
        baseline = copy.deepcopy(self.data)
        for mutation in ['incomplete', 'no_code', 'unknown_code', 'requirement_pending', 'check_pending']:
            with self.subTest(mutation=mutation):
                self.data = copy.deepcopy(baseline)
                if mutation == 'incomplete': self.item('S1 范围%')['work']['status'] = 'DOING'
                if mutation == 'no_code': del self.item('S1 范围%')['implementation_ids']
                if mutation == 'unknown_code': self.item('code1')['state'] = 'UNKNOWN'
                if mutation == 'requirement_pending': self.item('R1')['state'] = 'PENDING_HUMAN'
                if mutation == 'check_pending': self.item('V1')['state'] = 'GAP'
                self.assertEqual(self.row('R1')['verdict'], 'GAP')

    def test_all_nonpass_results_prevent_coverage(self):
        for result in ['FAIL', 'NOT_RUN', 'UNKNOWN']:
            self.item('V1')['work']['result'] = result
            self.assertEqual(self.row('R1')['verdict'], 'GAP')

    def test_partial_acceptance_cannot_hide_behind_a_passing_slice(self):
        self.item('R1')['work']['acceptance'].append('未命中时提供明确的界面提示。')
        row = self.row('R1')
        self.assertEqual(row['verdict'], 'GAP')
        self.assertEqual([a['passed'] for a in row['acceptance']], [True, False])
        self.assertTrue(any('验收条件 2' in p for p in row['gaps']))

    def test_missing_acceptance_mapping_is_a_visible_gap(self):
        self.item('V1')['work'].pop('acceptance_refs')
        self.assertIn('严格编号匹配回归：未关联具体验收条件', self.row('R1')['gaps'])

    def test_invalid_acceptance_mappings_are_rejected(self):
        for n, value in enumerate([[], {'R2':[1]}, {'R1':[0]}, {'R1':[2]}, {'R1':[True]}, {'R1':[]} ,{'R1':[1,1]}]):
            self.item('V1')['work']['acceptance_refs'] = value
            self.assertEqual(self.run_view('mapping'+str(n)).returncode, 1)

    def test_changed_or_missing_linked_sources_retract_green(self):
        for key in ['R1', 'S1 范围%', 'code1', 'V1']:
            p = self.root / self.item(key)['sources'][0]['path']
            original = p.read_bytes()
            for missing in [False, True]:
                with self.subTest(key=key, missing=missing):
                    if missing: p.unlink()
                    else: p.write_text('changed')
                    self.assertEqual(self.row('R1')['verdict'], 'RECHECK')
                    check = next(i for i in self.inspected if i['id'] == 'V1')
                    self.assertIn(check['freshness'], ['UNKNOWN', 'STALE'])
                    p.write_bytes(original)
        self.assertEqual(self.row('R1')['verdict'], 'COVERED')

    def test_dependency_readiness_propagates_even_when_downstream_says_done(self):
        self.item('S1 范围%')['work']['depends_on'] = ['S2']
        self.item('S2')['work']['depends_on'] = []
        self.assertEqual(self.row('R1')['verdict'], 'GAP')
        self.assertTrue(any('前置任务' in p for p in self.row('R1')['gaps']))

    def test_return_to_spec_retracts_downstream_coverage(self):
        self.data['lifecycle']['current_stage'] = 'Spec'
        self.assertEqual(self.row('R1')['verdict'], 'RECHECK')

    def test_stage_baseline_drift_withdraws_coverage(self):
        p = self.root / self.item('Spec')['sources'][0]['path']
        p.write_text('new requirement baseline, individual rows not yet reconciled')
        self.assertEqual(self.row('R1')['verdict'], 'RECHECK')

    def test_unconfirmed_predecessor_requirement_blocks_dependent_completion(self):
        self.item('S1 范围%')['work']['depends_on'] = ['S2']
        self.item('S2')['work']['depends_on'] = []
        self.item('S2')['work']['status'] = 'DONE'
        self.item('R2')['state'] = 'PENDING_HUMAN'
        self.assertTrue(any('前置任务' in p for p in self.row('R1')['gaps']))

    def test_missing_structured_links_remain_unknown(self):
        self.data['items'] = [i for i in self.data['items'] if i['id'] not in ['S1 范围%', 'V1']]
        for i in self.data['items']:
            if 'work' in i: i['work'].pop('depends_on', None)
        self.assertIn('尚未安排任务', self.row('R1')['gaps'])
        self.data['items'] = [i for i in self.data['items'] if 'work' not in i or i['work']['type'] == 'brief']
        self.data.pop('next_id')
        self.assertEqual(self.model()['covered'], 0)
        from project_view_lib.workstream_view import stats
        counts=stats(self.model())
        self.assertEqual(counts.count('未记录'),4)
        self.assertNotIn('0 / 0',counts)

    def test_bad_relations_and_malformed_data_rejected_before_output(self):
        baseline = copy.deepcopy(self.data)
        mutations = [
            ('S1 范围%', 'depends_on', ['missing']), ('S1 范围%', 'depends_on', ['R1']),
            ('S1 范围%', 'depends_on', ['S1 范围%']), ('S1 范围%', 'requirement_ids', []),
            ('V1', 'slice_ids', ['S2']), ('V1', 'result', 'SKIPPED'),
            ('R1', 'acceptance', []), ('R1', 'acceptance', 'a string'),
            ('S3', 'blocker', ''), ('R1', 'made_up', 'hidden'),
            ('S1 范围%', 'depends_on', ['S2']),
        ]
        for n, (key, field, value) in enumerate(mutations):
            with self.subTest(field=field, value=value):
                self.data = copy.deepcopy(baseline)
                self.item(key)['work'][field] = value
                run = self.run_view('bad' + str(n))
                self.assertEqual(run.returncode, 1, run.stdout)
                self.assertFalse((self.root / ('bad' + str(n))).exists())

    def test_planned_test_cannot_claim_runtime_pass(self):
        self.item('V1')['kind'] = 'design'
        self.assertEqual(self.run_view().returncode, 1)

    def test_unknown_work_without_lifecycle_or_sources_rejected(self):
        baseline = copy.deepcopy(self.data)
        for mode in ['stage', 'type', 'sources', 'lifecycle']:
            self.data = copy.deepcopy(baseline)
            if mode == 'stage': self.item('R1')['stage'] = 'Tasks'
            if mode == 'type': self.item('R1')['work'] = []
            if mode == 'sources': self.item('R1')['sources'] = []
            if mode == 'lifecycle': del self.data['lifecycle']
            self.assertEqual(self.run_view(mode).returncode, 1)

    def test_render_preserves_input_and_exposes_all_mainline_content(self):
        self.item('R1')['label'] = '<img src=x onerror=alert(1)>需求'
        self.assertEqual(self.run_view().returncode, 0)
        page = (self.root / 'v1/index.html').read_text()
        self.assertIn('data-initial-stage="Overview"', page)
        self.assertIn('data-coverage="R1" data-verdict="COVERED"', page)
        self.assertIn('data-slice-column="BLOCKED"', page)
        self.assertIn('验收条件', page)
        self.assertIn('&lt;img src=x onerror=alert(1)&gt;', page)
        self.assertNotIn('<img src=x', page)
        self.assertEqual(json.loads((self.root / 'v1/snapshot.json').read_text()), self.data)
        plain = (self.root / 'v1/view.md').read_text()
        self.assertIn('严格', plain)
        self.assertIn('NOT_RUN', plain)

    def test_immutable_update_rechecks_linked_sources_and_preserves_history(self):
        self.assertEqual(self.run_view().returncode, 0)
        before = (self.root / 'v1/index.html').read_bytes()
        p = self.root / self.item('R1')['sources'][0]['path']
        p.write_text('new contract')
        run = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'project_view.py'), 'update', '--root', str(self.root),
                              '--previous', str(self.root / 'v1'), '--output', str(self.root / 'v2')], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertEqual(before, (self.root / 'v1/index.html').read_bytes())
        receipt = json.loads((self.root / 'v2/receipt.json').read_text())
        self.assertTrue({'R1', 'S1 范围%', 'V1'} <= set(receipt['changes']['source_invalidated']))
        self.assertIn('data-verdict="RECHECK"', (self.root / 'v2/index.html').read_text())
