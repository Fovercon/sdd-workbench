from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name('audit_controller_access.py')


class ControllerAccessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.run = Path(self.tmp.name) / 'trial with spaces'
        (self.run / 'project').mkdir(parents=True)
        (self.run / 'runtime').mkdir()
        (self.run / 'input-receipt.json').write_text('{"synthetic":true}\n')

    def events(self, calls):
        events = []
        for i, (name, args, error) in enumerate(calls):
            events.append({'type': 'tool_execution_start', 'toolCallId': f'call-{i}',
                           'toolName': name, 'args': args})
            if error is not None:
                events.append({'type': 'tool_execution_end', 'toolCallId': f'call-{i}',
                               'toolName': name, 'isError': error,
                               'result': {'content': []}})
        events.append({'type': 'agent_end'})
        self.write(events)

    def write(self, events):
        (self.run / 'events.jsonl').write_text('\n'.join(map(json.dumps, events)) + '\n')

    def audit(self):
        before = {p: p.read_bytes() for p in self.run.rglob('*') if p.is_file()}
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), str(self.run)],
                                text=True, capture_output=True)
        self.assertTrue(result.stdout, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(before, {p: p.read_bytes() for p in self.run.rglob('*') if p.is_file()})
        self.assertTrue(payload['manual_review_required'])
        self.assertEqual(len(payload['auditor_sha256']), 64)
        if (self.run / 'events.jsonl').exists():
            self.assertEqual(payload['events_sha256'], hashlib.sha256(
                (self.run / 'events.jsonl').read_bytes()).hexdigest())
        return result.returncode, payload

    def test_literal_multifile_cat_keeps_exact_native_witness_and_completion(self):
        self.events([('bash', {'command': 'cat ../input-receipt.json ../variant.json'}, False)])
        code, result = self.audit()
        self.assertEqual(code, 1)
        self.assertEqual(result['status'], 'REQUESTS_FOUND')
        self.assertEqual([x['controller_file'] for x in result['findings']],
                         ['input-receipt.json', 'variant.json'])
        for item in result['findings']:
            self.assertEqual(item['tool_call_id'], 'call-0')
            self.assertEqual((item['start_line'], item['end_line']), (1, 2))
            self.assertIs(item['tool_is_error'], False)

    def test_cd_semicolon_newline_and_quoted_absolute_paths(self):
        command = f'cd "{self.run}"; cat repository.json\ncat "{self.run}/prompt.txt"'
        self.events([('bash', {'command': command}, False)])
        _, result = self.audit()
        self.assertEqual([x['controller_file'] for x in result['findings']],
                         ['repository.json', 'prompt.txt'])
        self.events([('bash', {'command': f'cd "{self.run}/project" && cat -- ../invocation.json'}, False)])
        self.assertEqual(self.audit()[1]['findings'][0]['controller_file'], 'invocation.json')

    def test_listing_printing_same_basename_and_runtime_are_not_controller_reads(self):
        self.events([
            ('bash', {'command': "echo 'cat ../variant.json'; ls ../input-receipt.json; cat variant.json"}, False),
            ('read', {'path': 'input-receipt.json'}, False),
            ('read', {'path': '../runtime/example/SKILL.md'}, False),
        ])
        code, result = self.audit()
        self.assertEqual((code, result['status']), (0, 'NO_REQUESTS_OBSERVED'))
        self.assertEqual(result['findings'], [])

    def test_quoted_shell_separators_remain_data(self):
        self.events([('bash', {'command': "echo ';' cat ../variant.json"}, False)])
        code, result = self.audit()
        self.assertEqual(code, 0)
        self.assertEqual(result['findings'], [])

    def test_dynamic_cd_previous_directory_is_not_a_literal_directory(self):
        self.events([('bash', {'command': 'cd -; cat ../../variant.json'}, False)])
        self.assertEqual(self.audit()[1]['findings'], [])

    def test_shell_word_concatenation_is_unclassified_instead_of_a_wrong_path(self):
        self.events([('bash', {'command': 'cat "../variant.json"other'}, False)])
        code, result = self.audit()
        self.assertEqual(code, 0)
        self.assertEqual(result['findings'], [])
        self.assertEqual(len(result['unclassified_calls']), 1)

    def test_structured_reader_and_failed_call_are_requests_not_success_proof(self):
        self.events([('read', {'path': '../project/../input-receipt.json'}, True)])
        code, result = self.audit()
        self.assertEqual(code, 1)
        self.assertIs(result['findings'][0]['tool_is_error'], True)
        self.assertEqual(result['findings'][0]['requested_path'], str(self.run / 'input-receipt.json'))

    def test_dynamic_shell_and_other_readers_remain_manual_without_execution(self):
        marker = self.run / 'must-not-run'
        self.events([
            ('bash', {'command': f'python3 -c "open(\'{marker}\',\'w\').write(\'x\')"'}, False),
            ('bash', {'command': 'cat "$ROOT/variant.json"'}, False),
            ('bash', {'command': 'cat <<EOF\n../input-receipt.json\nEOF'}, False),
            ('bash', {'command': '(cd ..; cat variant.json)'}, False),
        ])
        code, result = self.audit()
        self.assertEqual(code, 0)
        self.assertEqual(result['findings'], [])
        self.assertEqual(len(result['unclassified_calls']), 4)
        self.assertFalse(marker.exists())

    def test_pending_request_retains_finding_and_trace_is_incomplete(self):
        self.events([('read', {'path': '../variant.json'}, None)])
        code, result = self.audit()
        self.assertEqual((code, result['status']), (2, 'INVALID_OR_INCOMPLETE'))
        self.assertIsNone(result['findings'][0]['tool_is_error'])
        self.assertIsNone(result['findings'][0]['end_line'])

    def test_bad_json_empty_missing_terminal_duplicate_and_orphan_are_not_clean(self):
        cases = [[], [{'type': 'tool_execution_end', 'toolCallId': 'orphan', 'isError': False}, {'type': 'agent_end'}],
                 [{'type': 'message_end'}],
                 [{'type': 'tool_execution_start', 'toolCallId': 'same', 'toolName': 'read', 'args': {'path': 'SPEC.md'}},
                  {'type': 'tool_execution_start', 'toolCallId': 'same', 'toolName': 'read', 'args': {'path': 'PLAN.md'}},
                  {'type': 'agent_end'}]]
        for events in cases:
            with self.subTest(events=events):
                self.write(events)
                self.assertEqual(self.audit()[0], 2)
        (self.run / 'events.jsonl').write_bytes(b'{broken\n')
        self.assertEqual(self.audit()[0], 2)

    def test_assistant_claim_is_not_native_tool_execution(self):
        self.write([{'type': 'message_end', 'message': {'role': 'assistant', 'content': [
            {'type': 'text', 'text': 'cat ../variant.json was not executed'}]}}, {'type': 'agent_end'}])
        self.assertEqual(self.audit()[1]['findings'], [])

    def test_missing_log_has_no_process_evidence(self):
        code, result = self.audit()
        self.assertEqual((code, result['status']), (2, 'NOT_RECORDED'))
        self.assertIsNone(result['events_sha256'])

    def test_conditional_or_pipeline_cd_does_not_invent_a_controller_path(self):
        for command in ('echo x | cd ..; cat variant.json',
                        'cd .. || cat variant.json',
                        'false && cd ..; cat variant.json',
                        'cd .. && true; cat variant.json'):
            with self.subTest(command=command):
                self.events([('bash', {'command': command}, False)])
                code, result = self.audit()
                self.assertEqual(code, 0)
                self.assertEqual(result['findings'], [])
                self.assertTrue(result['unclassified_calls'])

    def test_prior_end_does_not_close_later_activity_but_a_new_end_does(self):
        activities = [
            [{'type': 'agent_start'}],
            [{'type': 'message_start'}],
            [{'type': 'message_end'}],
            [{'type': 'tool_execution_start', 'toolCallId': 'later', 'toolName': 'read', 'args': {'path': 'SPEC.md'}},
             {'type': 'tool_execution_end', 'toolCallId': 'later', 'toolName': 'read', 'isError': False}],
        ]
        for activity in activities:
            with self.subTest(activity=activity):
                events = [{'type': 'agent_end'}] + activity
                self.write(events)
                code, result = self.audit()
                self.assertEqual((code, result['status']), (2, 'INVALID_OR_INCOMPLETE'))
                self.write(events + [{'type': 'agent_end'}])
                self.assertEqual(self.audit()[0], 0)

    def test_completion_tool_identity_must_match_start_even_for_a_read_request(self):
        for name in (None, 'bash'):
            with self.subTest(name=name):
                self.events([('read', {'path': '../variant.json'}, False)])
                events = [json.loads(line) for line in (self.run / 'events.jsonl').read_text().splitlines()]
                if name is None:
                    del events[1]['toolName']
                else:
                    events[1]['toolName'] = name
                self.write(events)
                code, result = self.audit()
                self.assertEqual((code, result['status']), (2, 'INVALID_OR_INCOMPLETE'))
                self.assertIsNone(result['findings'][0]['tool_is_error'])
                self.assertIsNone(result['findings'][0]['end_line'])


if __name__ == '__main__':
    unittest.main()
