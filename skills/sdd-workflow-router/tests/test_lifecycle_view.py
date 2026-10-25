"""A lifecycle board must not invent stages or retain stale green claims."""
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET

CLI = Path(__file__).resolve().parents[1] / 'scripts/project_view.py'


class LifecycleViewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('rules.md', 'intent.md'):
            (self.root / name).write_text(name)
        self.data = {
            'project_id': 'platform', 'title': '配置治理平台样机',
            'scope': '当前只开展需求澄清', 'captured_at': '2026-10-20',
            'next_id': 'intent',
            'lifecycle': {'current_stage': 'Align',
                          'stage_items': {'Constitution': 'rules', 'Align': 'intent'}},
            'items': [self.record('rules', 'Constitution', '规则已经记录', 'rules.md'),
                      self.record('intent', 'Align', '确认输入和治理范围', 'intent.md')]
        }
        self.data['items'][1]['next'] = '确定治理样例与资料规范。'

    def record(self, key, stage, label, path):
        return {'id': key, 'label': label, 'stage': stage, 'view': 'progress',
                'kind': 'assessment', 'state': 'SATISFIED',
                'sources': [{'path': path, 'sha256': hashlib.sha256(
                    (self.root / path).read_bytes()).hexdigest()}]}

    def run_view(self, name='view'):
        source = self.root / 'input.json'
        source.write_text(json.dumps(self.data, ensure_ascii=False))
        return subprocess.run([sys.executable, '-B', str(CLI), 'render',
            '--root', str(self.root), '--input', str(source),
            '--output', str(self.root / name)], capture_output=True, text=True)

    def test_stage_order_and_progressive_empty_states(self):
        run = self.run_view()
        self.assertEqual(run.returncode, 0, run.stderr)
        page = (self.root / 'view/index.html').read_text()
        positions = [page.index(f'data-stage-nav="{stage}"') for stage in
                     ['Constitution', 'Align', 'Spec', 'Plan', 'Tasks', 'Implement', 'Converge', 'Finish']]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('Align · 需求澄清', page)
        self.assertIn('data-stage-status="NOT_STARTED"', page)
        self.assertIn('未开始', page)
        self.assertNotIn('还没有模块记录', page)
        self.assertNotIn('查看模块连接图', page)
        self.assertIn('当前阶段：Align', (self.root / 'view/view.md').read_text())

    def test_invalid_stage_mapping_is_rejected_before_output(self):
        cases = [
            {'current_stage': 'Requirements', 'stage_items': {'Align': 'intent'}},
            {'current_stage': 'Align', 'stage_items': {}},
            {'current_stage': 'Align', 'stage_items': {'Align': 'missing'}},
            {'current_stage': 'Align', 'stage_items': {'Align': 'rules'}},
            {'current_stage': 'Align', 'stage_items': {'Align': 'intent'}, 'completed': 7},
        ]
        for n, lifecycle in enumerate(cases):
            with self.subTest(lifecycle=lifecycle):
                self.data['lifecycle'] = lifecycle
                self.assertEqual(self.run_view(f'bad-{n}').returncode, 1)
                self.assertFalse((self.root / f'bad-{n}').exists())

    def test_stage_binding_requires_progress_and_sources(self):
        baseline = copy.deepcopy(self.data)
        for n, mutation in enumerate([{'view': 'capability'}, {'sources': []},
                                       {'stage': 'Plan'}]):
            self.data = copy.deepcopy(baseline)
            self.data['items'][1].update(mutation)
            self.assertEqual(self.run_view(f'bad-{n}').returncode, 1)

    def test_unknown_item_stage_is_not_silently_hidden(self):
        self.data['items'][0]['stage'] = 'Research'
        self.assertEqual(self.run_view().returncode, 1)

    def test_changed_current_stage_sources_remove_current_certainty(self):
        (self.root / 'intent.md').write_text('new user intent')
        run = self.run_view()
        self.assertEqual(run.returncode, 2, run.stderr)
        page = (self.root / 'view/index.html').read_text()
        self.assertIn('当前阶段需核对', page)
        self.assertIn('data-stage-status="STALE"', page)
        self.assertNotIn('data-stage-status="CURRENT"', page)

    def test_changed_earlier_stage_is_not_shown_as_complete(self):
        (self.root / 'rules.md').write_text('changed rules')
        run = self.run_view()
        self.assertEqual(run.returncode, 2, run.stderr)
        page = (self.root / 'view/index.html').read_text()
        self.assertIn('data-stage-status="STALE"', page)
        self.assertNotIn('data-stage-status="SATISFIED"', page)

    def test_returning_to_requirements_keeps_later_records_for_recheck(self):
        item = self.record('plan', 'Plan', '原设计', 'rules.md')
        item['kind'] = 'design'
        self.data['items'].append(item)
        self.data['lifecycle']['stage_items']['Plan'] = 'plan'
        run = self.run_view()
        self.assertEqual(run.returncode, 0, run.stderr)
        page = (self.root / 'view/index.html').read_text()
        self.assertIn('data-stage-status="REVISIT"', page)
        self.assertIn('待重新核对', page)
        self.assertIn('data-select="plan"', page)

    def test_missing_current_source_is_visible_and_not_current(self):
        (self.root / 'intent.md').unlink()
        run = self.run_view()
        self.assertEqual(run.returncode, 2, run.stderr)
        page = (self.root / 'view/index.html').read_text()
        self.assertIn('当前阶段需核对', page)
        self.assertIn('data-stage-status="UNKNOWN"', page)
        self.assertNotIn('data-stage-status="CURRENT"', page)

    def test_items_cannot_disappear_in_an_unbound_stage(self):
        extra = self.record('forgotten', 'Implement', '遗漏的阶段', 'rules.md')
        self.data['items'].append(extra)
        run = self.run_view()
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertFalse((self.root / 'view').exists())

    def test_relationship_to_a_file_record_from_an_earlier_stage_renders(self):
        self.data['lifecycle']['current_stage'] = 'Implement'
        self.data['lifecycle']['stage_items']['Implement'] = 'implementation'
        self.data['items'].append(self.record('implementation', 'Implement', '开发与测试', 'intent.md'))
        for key, stage, filename in [('before', 'Align', 'before.py'),
                                      ('after', 'Implement', 'after.py')]:
            (self.root / filename).write_text('sample')
            node = self.record(key, stage, filename, filename)
            node.update(view='structure', kind='code_observation', file=filename)
            self.data['items'].append(node)
        edge = self.record('call', 'Implement', '调用', 'after.py')
        edge.update(view='structure', kind='code_observation')
        edge.update({'from': 'before', 'to': 'after'})
        self.data['items'].append(edge)
        run = self.run_view()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('data-edge-id="call"', (self.root / 'view/index.html').read_text())

    def test_legacy_input_keeps_original_layout(self):
        self.data.pop('lifecycle')
        for item in self.data['items']:
            item.pop('stage')
        run = self.run_view()
        self.assertEqual(run.returncode, 0, run.stderr)
        page = (self.root / 'view/index.html').read_text()
        self.assertNotIn('data-stage-nav=', page)
        self.assertIn('做到哪了', page)
        self.assertIn('功能与分工', page)

    def test_each_stage_svg_owns_unique_arrow_markers_and_local_references(self):
        self.data['lifecycle']['current_stage'] = 'Implement'
        for stage in ('Plan', 'Implement'):
            key = stage.lower()
            self.data['lifecycle']['stage_items'][stage] = key
            self.data['items'].append(self.record(key, stage, stage, 'rules.md'))
            for suffix in ('input', 'output'):
                node = self.record(f'{key}-{suffix}', stage, suffix, 'rules.md')
                node.update(view='structure', kind='design')
                self.data['items'].append(node)
            edge = self.record(f'{key}-edge', stage, '处理资料', 'rules.md')
            edge.update(view='structure', kind='design',
                        **{'from': f'{key}-input', 'to': f'{key}-output'})
            self.data['items'].append(edge)
        run = self.run_view()
        self.assertEqual(run.returncode, 0, run.stderr)
        page = (self.root / 'view/index.html').read_text()
        diagrams = [ET.fromstring(svg) for svg in re.findall(r'<svg\b.*?</svg>', page)]
        self.assertEqual(len(diagrams), 2)
        ids = [marker.attrib['id'] for svg in diagrams for marker in svg.findall('.//marker')]
        self.assertEqual(len(ids), len(set(ids)),
                         'Hidden earlier-stage SVG must not own a later-stage arrow reference')
        for svg in diagrams:
            local_ids = {marker.attrib['id'] for marker in svg.findall('.//marker')}
            edges = svg.findall("path[@class='edge']")
            self.assertEqual(len(edges), 1)
            for edge in edges:
                self.assertIn(edge.attrib['marker-end'], {f'url(#{key})' for key in local_ids})


if __name__ == '__main__':
    unittest.main()
