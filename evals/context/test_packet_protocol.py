"""The forward oracle must accept manual excerpts and expose missing obligations."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import prepare_packet
from prepare_packet import prepare

CLI = Path(__file__).with_name('prepare_packet.py')


class PacketProtocolTests(unittest.TestCase):
    def test_preparer_preserves_declared_bytes_under_newline_translation(self):
        write_text = Path.write_text
        def windows_write(path, text, *args, **kwargs):
            return write_text(path, text.replace('\n', '\r\n'), *args, **kwargs)
        trial = Path(self.tmp.name) / 'translated'
        with patch.object(Path, 'write_text', windows_write):
            prepare(trial)
        variant = json.loads((trial / 'variant.json').read_text(encoding='utf-8'))
        self.assertEqual(hashlib.sha256((trial / 'prompt.txt').read_bytes()).hexdigest(),
                         variant['prompt_sha256'])
        selection = json.loads((trial / 'project/selection.json').read_text(encoding='utf-8'))
        for source in selection['sources']:
            self.assertEqual(hashlib.sha256((trial / 'project' / source['path']).read_bytes()).hexdigest(),
                             source['expected_sha256'])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.run = (Path(self.tmp.name) / 'trial').resolve()
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

    def native_read(self, path, error=False):
        return [
            {'type': 'tool_execution_start', 'toolCallId': 'read-1',
             'toolName': 'read', 'args': {'path': path}},
            {'type': 'tool_execution_end', 'toolCallId': 'read-1',
             'toolName': 'read', 'isError': error, 'result': {'content': []}},
            {'type': 'agent_end'},
        ]

    def write_events(self, events):
        (self.run / 'events.jsonl').write_text(
            '\n'.join(map(json.dumps, events)) + '\n', encoding='utf-8')

    def test_correct_packet_fails_after_controller_read_request(self):
        self.manual_packet()
        for name, error in (('input-receipt.json', False), ('prompt.txt', True),
                            ('packet-evaluation.json', False)):
            with self.subTest(name=name, error=error):
                path = (self.run / name).as_posix()
                self.write_events(self.native_read(path, error))
                result, report = self.evaluate()
                self.assertEqual(result.returncode, 1)
                self.assertEqual(report['automated_guards'], 'FAIL')
                self.assertTrue(report['protected_sources_unchanged'])
                self.assertEqual(report['native_controller_access']['status'], 'REQUESTS_FOUND')
                finding = report['native_controller_access']['findings'][0]
                self.assertEqual(finding['controller_file'], name)
                self.assertEqual((finding['start_line'], finding['end_line']), (1, 2))
                self.assertIs(finding['tool_is_error'], error)

    def test_correct_packet_fails_with_invalid_or_unfinished_native_events(self):
        self.manual_packet()
        for stream in ('', 'not json\n', json.dumps(self.native_read('spec.md')[0]) + '\n'):
            with self.subTest(stream=stream):
                (self.run / 'events.jsonl').write_text(stream, encoding='utf-8')
                result, report = self.evaluate()
                self.assertEqual(result.returncode, 1)
                self.assertEqual(report['native_controller_access']['status'], 'INVALID_OR_INCOMPLETE')

    def test_correct_packet_keeps_permitted_source_read_distinct_from_controller_read(self):
        self.manual_packet()
        self.write_events(self.native_read('spec.md'))
        result, report = self.evaluate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('native_controller_access', report)
        self.assertEqual(report['native_controller_access']['status'], 'NO_REQUESTS_OBSERVED')

    def test_inspection_preserves_raw_events_and_historical_report(self):
        self.manual_packet()
        self.write_events(self.native_read('../prompt.txt'))
        (self.run / 'packet-evaluation.json').write_bytes(b'{"historical":"PASS"}\n')
        before = {p.relative_to(self.run): p.read_bytes() for p in self.run.rglob('*') if p.is_file()}
        self.assertTrue(callable(getattr(prepare_packet, 'inspect_packet', None)),
                        'Packet inspection needs a read-only replay entry point')
        report = prepare_packet.inspect_packet(self.run)
        self.assertEqual(report['automated_guards'], 'FAIL')
        self.assertEqual(report['native_controller_access']['status'], 'REQUESTS_FOUND')
        self.assertEqual(before, {p.relative_to(self.run): p.read_bytes()
                                  for p in self.run.rglob('*') if p.is_file()})

    def test_oracle_accepts_manual_correct_packet_without_requiring_candidate_format(self):
        self.manual_packet()
        result, report = self.evaluate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report['automated_guards'], 'PASS')
        self.assertTrue(report['protected_sources_unchanged'])
        self.assertIn('native_controller_access', report)
        self.assertEqual(report['native_controller_access']['status'], 'NOT_RECORDED')

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
