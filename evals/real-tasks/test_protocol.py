"""Run explicitly from the source checkout; this evaluator is not a plugin input."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


prepare = module('prepare')
probe = module('probe')
usage = module('usage')


class RealTaskProtocol(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sdd-real-protocol-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def test_same_inputs_across_hosts_and_runtime_without_oracles(self):
        left = prepare.prepare('adapter', self.base / 'left', 'pi')
        right = prepare.prepare('adapter', self.base / 'right', 'codex')
        a = json.loads((left / 'receipt.json').read_text(encoding='utf-8'))
        b = json.loads((right / 'receipt.json').read_text(encoding='utf-8'))
        self.assertEqual(a['inputs'], b['inputs'])
        self.assertEqual(a['runtime_skills'], b['runtime_skills'])
        self.assertEqual(a['company_representativeness'], 'NOT_ESTABLISHED')
        self.assertEqual(len(list((left / 'runtime-skills').glob('*/SKILL.md'))), 12)
        self.assertTrue(a['runtime_skills'])
        for name in a['runtime_skills']:
            self.assertNotIn('evals', Path(name).parts)
            self.assertNotIn('tests', Path(name).parts)

    def test_oracle_rejects_original_failure_and_accepts_released_repair(self):
        baseline = prepare.prepare('encoding', self.base / 'baseline', 'calibration')
        failed = probe.encoding(baseline / 'project')
        self.assertEqual(len(failed), 5)
        self.assertFalse(any(value['pass'] for value in failed), failed)
        released = self.base / 'released'
        released.mkdir()
        prepare.extract(prepare.SUITE, released)
        passed = probe.encoding(released)
        self.assertTrue(all(value['pass'] for value in passed), passed)

    def test_readonly_protection_and_git_identity_are_not_model_judgements(self):
        trial = prepare.prepare('adapter', self.base / 'readonly', 'pi')
        self.assertTrue(probe.preservation(trial)['pass'])
        (trial / 'project/adapters/deepseek.mjs').write_text('modified', encoding='utf-8')
        (trial / 'project/unauthorized.txt').write_text('extra', encoding='utf-8')
        report = probe.preservation(trial)
        self.assertFalse(report['pass'])
        self.assertIn('readonly input changed: adapters/deepseek.mjs', report['errors'])
        self.assertIn('unauthorized addition: unauthorized.txt', report['errors'])

    def test_existing_output_and_checkout_are_never_overwritten(self):
        destination = self.base / 'existing'
        destination.mkdir()
        marker = destination / 'keep'
        marker.write_bytes(b'user work')
        with self.assertRaises(FileExistsError):
            prepare.prepare('adapter', destination, 'pi')
        self.assertEqual(marker.read_bytes(), b'user work')
        with self.assertRaises(ValueError):
            prepare.prepare('adapter', prepare.ROOT / '.eval-artifacts/should-not-exist', 'pi')


class UsageProtocol(unittest.TestCase):
    def run_events(self, host, events):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'events.jsonl'
            path.write_text('\n'.join(json.dumps(value) for value in events) + '\n', encoding='utf-8')
            return usage.summarize(host, path)[0]

    def test_pi_streaming_deltas_and_reasoning_are_not_double_counted(self):
        report = self.run_events('pi', [
            {'type': 'message_update', 'usage': {'output': 10000}},
            {'type': 'message_end', 'message': {'role': 'assistant', 'provider': 'p', 'model': 'm',
                'usage': {'input': 10, 'output': 5, 'cacheRead': 20, 'reasoning': 2, 'totalTokens': 35}}},
            {'type': 'message_end', 'message': {'role': 'assistant', 'provider': 'p', 'model': 'm',
                'usage': {'input': 3, 'output': 4, 'cacheRead': 30, 'totalTokens': 37}}},
            {'type': 'tool_execution_end', 'isError': True}, {'type': 'agent_end'},
        ])
        self.assertEqual(report['reported_token_totals'],
                         {'input': 13, 'output': 9, 'cacheRead': 50, 'reasoning': 2, 'totalTokens': 72})
        self.assertEqual(report['field_observation_counts']['reasoning'], 1)
        self.assertNotIn('cacheWrite', report['reported_token_totals'])
        self.assertEqual(report['nonzero_commands_or_tool_errors'], 1)

    def test_codex_only_counts_completed_turns_and_keeps_cache_subset(self):
        report = self.run_events('codex', [
            {'type': 'item.completed', 'usage': {'input_tokens': 99999},
             'item': {'type': 'command_execution', 'exit_code': 1}},
            {'type': 'turn.completed', 'usage': {
                'input_tokens': 100, 'cached_input_tokens': 70, 'output_tokens': 8,
                'reasoning_output_tokens': 3}},
        ])
        self.assertEqual(report['reported_token_totals']['input_tokens'], 100)
        self.assertEqual(report['reported_token_totals']['cached_input_tokens'], 70)
        self.assertEqual(report['reported_token_totals']['output_tokens'], 8)
        self.assertEqual(report['completed_usage_events'], 1)

    def test_interrupted_missing_usage_is_not_zero_or_completion(self):
        report = self.run_events('pi', [
            {'type': 'message_end', 'message': {'role': 'assistant', 'model': 'm', 'provider': 'p'}}])
        self.assertFalse(report['native_completion_event_observed'])
        self.assertEqual(report['completed_messages_without_usage'], 1)
        self.assertEqual(report['reported_token_totals'], {})

    def test_truncated_stream_retains_completed_usage_and_marks_corruption(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'events.jsonl'
            complete = {'type': 'turn.completed', 'usage': {'input_tokens': 10, 'output_tokens': 2}}
            path.write_bytes(json.dumps(complete).encode() + b'\nnull\n{"type":"partial-\xe4')
            report, _ = usage.summarize('codex', path)
        self.assertFalse(report['raw_stream_valid_utf8'])
        self.assertEqual(report['malformed_json_lines'], [2, 3])
        self.assertEqual(report['reported_token_totals'], {'input_tokens': 10, 'output_tokens': 2})


if __name__ == '__main__':
    unittest.main()
