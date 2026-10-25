"""Contract sources, offline runtime and immutable receipts survive diagram rendering."""
import base64
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLI = Path(__file__).resolve().parents[1] / 'scripts/project_view.py'


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.csp = None
        self.scripts = []
        self.inside = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('http-equiv') == 'Content-Security-Policy':
            self.csp = attrs['content']
        if tag == 'script':
            self.inside = True
            self.scripts.append('')

    def handle_endtag(self, tag):
        if tag == 'script':
            self.inside = False

    def handle_data(self, data):
        if self.inside:
            self.scripts[-1] += data


class DesignViewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def render(self, source, name='v1', lifecycle=False, technical=None):
        contract = self.root / 'plan.md'
        contract.write_text('```mermaid\n' + source + '\n```\n')
        if technical:
            contract.write_text(contract.read_text() + '\n```mermaid\n' + technical + '\n```\n')
        ref = {'path': 'plan.md', 'line': 2, 'sha256': hashlib.sha256(contract.read_bytes()).hexdigest()}
        data = {'project_id': 'design', 'title': '设计评审', 'scope': '仅设计',
                'captured_at': '2026-10-21', 'items': [
                    {'id': 'view', 'label': '待评审设计', 'view': 'design', 'kind': 'design',
                     'state': 'PENDING_HUMAN', 'mermaid': source, 'sources': [ref]}]}
        if lifecycle:
            data['items'][0]['stage'] = 'Plan'
            data['items'].append({'id': 'gate', 'label': '等待设计评审', 'view': 'progress',
                'stage': 'Plan', 'kind': 'assessment', 'state': 'PENDING_HUMAN', 'sources': [ref]})
            data['lifecycle'] = {'current_stage': 'Plan', 'stage_items': {'Plan': 'gate'}}
        if technical is not None:
            data['items'][0]['technical_mermaid'] = technical
        inp = self.root / 'input.json'
        inp.write_text(json.dumps(data))
        output = self.root / name
        run = subprocess.run([sys.executable, '-B', str(CLI), 'render', '--root', str(self.root),
            '--input', str(inp), '--output', str(output)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        return output, contract

    def test_all_families_keep_contract_and_pending_state_in_both_boards(self):
        sources = ['flowchart LR\nA --> B', 'sequenceDiagram\nA->>B: 请求',
                   'stateDiagram-v2\n[*] --> Ready', 'classDiagram\nclass Engine',
                   'erDiagram\nTASK ||--o{ UNIT : owns']
        for mode in (False, True):
            for n, source in enumerate(sources):
                with self.subTest(mode=mode, source=source):
                    output, contract = self.render(source, f'{mode}-{n}', mode)
                    before = contract.read_bytes()
                    page = (output / 'index.html').read_text()
                    self.assertIn('data-design-source', page)
                    self.assertIn('data-state="PENDING_HUMAN"', page)
                    self.assertEqual(json.loads((output / 'snapshot.json').read_text())['items'][0]['mermaid'], source)
                    self.assertIn('\n'.join('    ' + line for line in source.splitlines()),
                                  (output / 'view.md').read_text())
                    self.assertEqual(contract.read_bytes(), before)
                    receipt = json.loads((output / 'receipt.json').read_text())
                    self.assertIn('project_view_lib/vendor/mermaid-12.2.0.min.js.gz', receipt['generator'])
                    for name, digest in receipt['files'].items():
                        self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), digest)

    def test_script_like_contract_cannot_terminate_script_or_break_csp(self):
        source = 'flowchart LR\nA["</script><script>window.INJECTED=1</script>"] --> B'
        output, _ = self.render(source)
        page = (output / 'index.html').read_text()
        doc = Document(page)
        self.assertEqual(len(doc.scripts), 1)
        digest = base64.b64encode(hashlib.sha256(doc.scripts[0].encode()).digest()).decode()
        self.assertIn("'sha256-" + digest + "'", doc.csp)
        self.assertNotIn('unsafe-eval', doc.csp)
        self.assertIn('&lt;/script&gt;', page)

    def test_overview_and_technical_sources_are_preserved_separately(self):
        source='flowchart LR\nENGINE[治理引擎] --> DOC[文档片段]'
        technical='classDiagram\nclass GovernanceEngine {\n+parse_units(str text) Unit\n}'
        output,contract=self.render(source,technical=technical,lifecycle=True)
        data=json.loads((output/'snapshot.json').read_text())['items'][0]
        self.assertEqual(data['mermaid'],source)
        self.assertEqual(data['technical_mermaid'],technical)
        self.assertIn(source,contract.read_text())
        self.assertIn(technical,contract.read_text())
        page=(output/'index.html').read_text()
        self.assertIn('class="design-gallery"',page)
        self.assertIn('data-design-card="view"',page)
        self.assertIn('class="design-technical"',page)
        self.assertIn('data-technical="true"',page)
        self.assertIn('technical_mermaid', (output/'snapshot.json').read_text())


if __name__ == '__main__':
    unittest.main()
