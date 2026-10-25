"""A separately delivered diagram is useful only with its source identity."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLI = Path(__file__).resolve().parents[1] / 'scripts/project_view.py'


class DiagramViewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'process.html').write_text('<html>独立流程图</html>')
        (self.root / 'process.py').write_text('current implementation')
        self.data = {
            'project_id': 'loan', 'title': '设备借用', 'scope': '借用流程',
            'captured_at': '2026-10-20',
            'items': [{
                'id': 'borrow', 'label': '借用怎样完成', 'view': 'diagram',
                'kind': 'code_observation', 'state': 'SATISFIED',
                'artifact': 'process.html', 'note': '登记、核对、保存借用记录。',
                'sources': [{'path': name, 'sha256': hashlib.sha256(
                    (self.root / name).read_bytes()).hexdigest()}
                    for name in ('process.html', 'process.py')]
            }]
        }

    def run_view(self, name='view', *extra):
        source = self.root / 'input.json'
        source.write_text(json.dumps(self.data, ensure_ascii=False))
        return subprocess.run([sys.executable, '-B', str(CLI), 'render',
            '--root', str(self.root), '--input', str(source),
            '--output', str(self.root / name), *extra], capture_output=True, text=True)

    def test_diagram_opens_separately_and_keeps_its_evidence(self):
        run = self.run_view()
        self.assertEqual(run.returncode, 0, run.stderr)
        html = (self.root / 'view/index.html').read_text()
        self.assertIn('href="../process.html"', html)
        self.assertIn('class="diagram-open"', html)
        self.assertIn('data-select="borrow"', html)
        self.assertNotIn('<iframe', html)
        self.assertNotIn('data-node-id="borrow"', html)
        self.assertIn(r'process\.html', (self.root / 'view/view.md').read_text())

    def test_changed_code_or_diagram_invalidates_the_diagram(self):
        for name in ('process.py', 'process.html'):
            with self.subTest(name=name):
                path = self.root / name
                before = path.read_bytes()
                path.write_text('changed')
                run = self.run_view(name + '-view')
                self.assertEqual(run.returncode, 2, run.stderr)
                receipt = json.loads((self.root / (name + '-view/receipt.json')).read_text())
                self.assertEqual(receipt['items'][0]['effective_state'], 'STALE')
                html = (self.root / (name + '-view/index.html')).read_text()
                self.assertNotIn('class="diagram-open"', html)
                self.assertIn('data-select="borrow"', html)
                path.write_bytes(before)

    def test_artifact_and_load_bearing_sources_must_be_cited(self):
        baseline = copy.deepcopy(self.data)
        for sources in [[], baseline['items'][0]['sources'][:1],
                        baseline['items'][0]['sources'][1:]]:
            self.data = copy.deepcopy(baseline)
            self.data['items'][0]['sources'] = sources
            run = self.run_view()
            self.assertEqual(run.returncode, 1)
            self.assertFalse((self.root / 'view').exists())

    def test_artifact_cannot_escape_root_even_via_symlink(self):
        outside = self.root.parent / (self.root.name + '-outside.html')
        outside.write_text('outside')
        self.addCleanup(lambda: outside.unlink(missing_ok=True))
        (self.root / 'alias.html').symlink_to(outside)
        for name in ('../' + outside.name, 'alias.html'):
            self.data['items'][0]['artifact'] = name
            self.data['items'][0]['sources'][0]['path'] = name
            run = self.run_view()
            self.assertEqual(run.returncode, 1)

    def test_missing_diagram_is_unknown_and_has_no_primary_open_link(self):
        (self.root / 'process.html').unlink()
        run = self.run_view()
        self.assertEqual(run.returncode, 2)
        receipt = json.loads((self.root / 'view/receipt.json').read_text())
        self.assertEqual(receipt['items'][0]['effective_state'], 'UNKNOWN')
        self.assertNotIn('class="diagram-open"', (self.root / 'view/index.html').read_text())

    def test_diagram_fields_are_not_silently_ignored_on_other_views(self):
        self.data['items'][0]['view'] = 'capability'
        self.assertEqual(self.run_view().returncode, 1)


if __name__ == '__main__':
    unittest.main()
