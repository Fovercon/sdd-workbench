"""The forward oracle must accept manual excerpts and expose missing obligations."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLI = Path(__file__).with_name('prepare_packet.py')


class PacketProtocolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.run = Path(self.tmp.name) / 'trial'
        result = self.call('prepare', '--output', self.run)
        self.assertEqual(result.returncode, 0, result.stderr)

    def call(self, *args):
        return subprocess.run([sys.executable, '-B', str(CLI), *map(str, args)], capture_output=True)

    def manual_packet(self):
        project = self.run / 'project'
        packet = project / 'packet'
        packet.mkdir()
        (packet / 'context.md').write_text(
            'Synthetic; no implementation or approval authority.\n'
            'Source files must remain unchanged.\n'
            'FR-007: Retry selected failed units only.\n'
            'AC-007.1: Successful output bytes and modification times stay unchanged.\n'
            'Shared invariant: all task writes require the same task lock.\n'
            'Current slice S2: expose the existing retry action; do not change its semantics.\n',
            encoding='utf-8')
        receipt = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in project.iterdir() if p.is_file() and p.name != 'selection.json'}
        (packet / 'sources.json').write_text(json.dumps(receipt), encoding='utf-8')

    def evaluate(self):
        result = self.call('evaluate', self.run)
        return result, json.loads(result.stdout)

    def test_oracle_accepts_manual_correct_packet_without_requiring_candidate_format(self):
        self.manual_packet()
        result, report = self.evaluate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report['automated_guards'], 'PASS')
        self.assertTrue(report['protected_sources_unchanged'])

    def test_oracle_rejects_missing_shared_obligation_and_modified_source(self):
        self.manual_packet()
        context = self.run / 'project/packet/context.md'
        context.write_text(context.read_text().replace(
            'Shared invariant: all task writes require the same task lock.\n', ''), encoding='utf-8')
        result, report = self.evaluate()
        self.assertEqual(result.returncode, 1)
        self.assertIn('Missing shared obligation', report['errors'])
        (self.run / 'project/spec.md').write_text('Changed', encoding='utf-8')
        result, report = self.evaluate()
        self.assertFalse(report['protected_sources_unchanged'])

    def test_oracle_rejects_unrelated_history_or_budget_overflow(self):
        self.manual_packet()
        context = self.run / 'project/packet/context.md'
        original = context.read_bytes()
        for suffix in (b'UNRELATED_HISTORY_Z9', b'x' * 4096):
            context.write_bytes(original + suffix)
            result, report = self.evaluate()
            self.assertEqual(result.returncode, 1)
            self.assertEqual(report['automated_guards'], 'FAIL')

    def test_preparer_refuses_reuse_and_same_task_inputs_match_frozen_release(self):
        self.assertNotEqual(self.call('prepare', '--output', self.run).returncode, 0)
        old = Path(self.tmp.name) / 'old'
        result = self.call('prepare', '--output', old, '--ref', 'v0.5.0')
        self.assertEqual(result.returncode, 0, result.stderr)
        current = json.loads((self.run / 'input-receipt.json').read_text())
        baseline = json.loads((old / 'input-receipt.json').read_text())
        self.assertEqual(current['project'], baseline['project'])
        self.assertEqual((self.run / 'prompt.txt').read_bytes(), (old / 'prompt.txt').read_bytes())


if __name__ == '__main__':
    unittest.main()
