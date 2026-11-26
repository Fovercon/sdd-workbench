"""events.py parser self-tests: Pi 1.3.0 shapes plus legacy 0.86 fallback."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from runner import events  # noqa: E402


def write(lines):
    with tempfile.NamedTemporaryFile('w', suffix='.jsonl', delete=False, encoding='utf-8') as fh:
        for line in lines:
            fh.write(line + '\n')
        return Path(fh.name)


PI13 = [
    '{"type":"session"}',
    '{"type":"message_update","usage":{"input":0,"output":0},"assistantMessageEvent":{"type":"text_delta","text":"片段"}}',
    '{"type":"message_end","message":{"role":"system","content":"","usage":{"input":900,"cacheRead":100,"cacheWrite":10,"output":0,"totalTokens":1010}}}',
    '{"type":"message_end","message":{"role":"assistant","content":[{"type":"text","text":"计划如下"}],"usage":{"input":200,"output":50}}}',
    '{"type":"message_end","message":{"role":"assistant","content":[{"type":"toolCall","name":"read","arguments":{"path":"/rt/sdd-plan-slices/SKILL.md"}},{"type":"toolCall","name":"bash","arguments":{"command":"cat ../runtime/sdd-implement-slice/SKILL.md"}}],"usage":{"input":300,"output":80}}}',
    '{"type":"message_end","message":{"role":"assistant","content":[{"type":"text","text":"SLICE_COMPLETE"}],"usage":{"input":150,"output":20}}}',
    'not json',
    '{"type":"brand_new_event","payload":1}',
]

LEGACY = [
    '{"type":"message_end","usage":{"input":10,"output":5},"message":{"role":"assistant","text":"旧格式答复"}}',
    '{"type":"tool_call","tool":"read","args":{"path":"../runtime/sdd-code-review/SKILL.md"}}',
]


class TestParsePi13(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parsed = events.parse(write(PI13))

    def test_usage_only_from_message_end(self):
        usage = self.parsed['usage']
        self.assertEqual(usage['usage_events'], 3)
        self.assertEqual(usage['input'], 200 + 300 + 150)
        self.assertEqual(usage['input_peak'], 300)
        self.assertEqual(usage['cache_read'], 0)
        self.assertEqual(usage['cache_write'], 0)
        self.assertEqual(usage['output'], 150)

    def test_streaming_deltas_ignored_for_text(self):
        self.assertEqual(self.parsed['final_text'], 'SLICE_COMPLETE')

    def test_reads_deduped_with_bash_skill_paths(self):
        targets = {(r['tool'], r['path']) for r in self.parsed['reads']}
        self.assertIn(('read', '/rt/sdd-plan-slices/SKILL.md'), targets)
        self.assertIn(('bash', 'runtime/sdd-implement-slice/'), targets)
        self.assertEqual(len(self.parsed['reads']), 2)

    def test_parse_errors_and_unknowns_counted(self):
        self.assertEqual(self.parsed['parse_errors'], 1)
        self.assertEqual(self.parsed['unknown_types'].get('brand_new_event'), 1)


class TestParseLegacy(unittest.TestCase):
    def test_tool_result_structured_text_is_supported(self):
        parsed = events.parse(write([json.dumps({'type': 'tool_execution_end',
            'toolCallId': 'c', 'isError': False, 'result': {'structuredContent': 'read content'}})]))
        self.assertTrue(parsed['tool_results']['c'])

    def test_legacy_usage_and_text(self):
        parsed = events.parse(write(LEGACY))
        self.assertEqual(parsed['usage']['input'], 10)
        self.assertEqual(parsed['usage']['output'], 5)
        self.assertEqual(parsed['final_text'], '旧格式答复')
        self.assertEqual(parsed['reads'][0]['path'], '../runtime/sdd-code-review/SKILL.md')


class TestUsageAccounting(unittest.TestCase):
    def parse(self, rows):
        path = write([json.dumps(row) for row in rows])
        self.addCleanup(path.unlink)
        return events.parse(path)['usage']

    def message(self, text='one'):
        return {'role': 'assistant', 'text': text,
                'usage': {'input': 11, 'output': 7, 'cacheRead': 3, 'cacheWrite': 2}}

    def test_message_end_and_turn_end_mirror_count_once(self):
        message = self.message()
        usage = self.parse([{'type': 'message_end', 'message': message},
                            {'type': 'turn_end', 'message': message}])
        self.assertEqual({k: usage[k] for k in ('input','output','cache_read','cache_write','usage_events','input_peak')},
                         {'input': 11,'output': 7,'cache_read': 3,'cache_write': 2,'usage_events': 1,'input_peak': 11})

    def test_distinct_requests_with_equal_usage_both_count(self):
        rows = []
        for text in ('one', 'two'):
            message = self.message(text)
            rows.extend([{'type': 'message_end', 'message': message},
                         {'type': 'turn_end', 'message': message}])
        usage = self.parse(rows)
        self.assertEqual((usage['input'], usage['output'], usage['usage_events']), (22, 14, 2))

    def test_legacy_turn_end_only_usage_and_peak(self):
        usage = self.parse([{'type': 'turn_end', 'usage': {'input_tokens': 17,'completion_tokens': 5}},
                            {'type': 'turn_end', 'message': self.message()}])
        self.assertEqual((usage['input'],usage['output'],usage['input_peak'],usage['usage_events']), (28,12,17,2))

    def test_mixed_native_and_legacy_turns_do_not_drop_legacy_usage(self):
        message = self.message()
        usage = self.parse([{'type': 'message_end','message': message},
                            {'type': 'turn_end','message': message},
                            {'type': 'turn_end','usage': {'input': 17,'output': 5}}])
        self.assertEqual((usage['input'],usage['output'],usage['usage_events']), (28,12,2))

    def test_result_summary_does_not_add_to_per_message_usage(self):
        usage = self.parse([{'type': 'message_end','message': self.message()},
                            {'type': 'result','usage': {'input': 11,'output': 7}}])
        self.assertEqual((usage['input'],usage['output'],usage['usage_events']), (11,7,1))

    def test_result_only_legacy_fallback_is_reported(self):
        usage = self.parse([{'type': 'result','usage': {'input': 17,'output': 5}}])
        self.assertEqual((usage['input'],usage['output'],usage['usage_events']), (17,5,1))
        self.assertTrue(usage['complete'])

    def test_unknown_usage_is_unavailable_instead_of_reported_as_free(self):
        for row in ({'type': 'message_end','message': {'role':'assistant','usage': {'tokens':999}}},
                    {'type':'future_usage','usage': {'input':99}},
                    {'type':'message_end','message': {'role':'assistant','text':'missing usage'}}):
            with self.subTest(row=row):
                usage = self.parse([row])
                self.assertFalse(usage['complete'])
                self.assertGreater(usage['unclassified_usage_events'], 0)


class TestDetectSkills(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.runtime = Path(self.tmp.name) / 'runtime'
        for skill in ('sdd-plan-slices', 'sdd-implement-slice', 'sdd-code-review'):
            (self.runtime / skill).mkdir(parents=True)
            (self.runtime / skill / 'SKILL.md').write_text('# Skill')
            (self.runtime / skill / 'references').mkdir()
            (self.runtime / skill / 'references/model.md').write_text('# Model')
        self.project = Path(self.tmp.name) / 'project'
        self.project.mkdir()

    def command(self, command, *, failed=False, exit_code=0):
        path = Path(self.tmp.name) / 'events.jsonl'
        rows = [
            {'type': 'message_end', 'message': {'role': 'assistant', 'content': [
                {'type': 'toolCall', 'id': 'c1', 'name': 'bash',
                 'arguments': {'command': command}}]}},
            {'type': 'tool_execution_end', 'toolCallId': 'c1', 'isError': failed,
             'result': {'structuredContent': {'exit_code': exit_code}}},
        ]
        path.write_text('\n'.join(json.dumps(r) for r in rows), encoding='utf-8')
        return events.detect_skills(events.parse(path), self.runtime, self.project)

    def test_cd_then_read_skill_and_reference(self):
        for command in (
            f'cd {self.runtime}/sdd-plan-slices && cat SKILL.md',
            f'cd {self.runtime}; cat sdd-plan-slices/SKILL.md',
            f'cd {self.runtime}/sdd-plan-slices; sed -n 1,40p references/model.md',
        ):
            with self.subTest(command=command):
                self.assertEqual(self.command(command), ['sdd-plan-slices'])

    def test_listing_and_echoing_skill_paths_are_not_reads(self):
        for command in (f'ls {self.runtime}/sdd-plan-slices/',
                        f'echo {self.runtime}/sdd-plan-slices/SKILL.md',
                        f'cd {self.runtime}/sdd-plan-slices && pwd',
                        f'cat {self.runtime}/sdd-plan-slices-extra/SKILL.md'):
            with self.subTest(command=command):
                self.assertEqual(self.command(command), [])

    def test_failed_command_does_not_count_as_read(self):
        cmd = f'cat {self.runtime}/sdd-plan-slices/SKILL.md'
        self.assertEqual(self.command(cmd, failed=True), [])
        self.assertEqual(self.command(cmd, exit_code=1), [])

    def test_success_of_compound_command_does_not_prove_skipped_read(self):
        marker = self.runtime / 'sdd-plan-slices' / 'SKILL.md'
        self.assertEqual(self.command(f'false && cat {marker}; true'), [])
        marker.unlink()
        self.assertEqual(self.command(f'cat {marker} 2>/dev/null | head -5'), [])

    def test_patterns_and_heredocs_are_not_file_reads(self):
        marker = self.runtime / 'sdd-plan-slices' / 'SKILL.md'
        self.assertEqual(self.command(f'grep -F {marker} README.md'), [])
        self.assertEqual(self.command(f"cat > notes.md <<'EOF'\ncat {marker}\nEOF"), [])

    def test_quoted_directory(self):
        directory = self.runtime.parent / 'runtime with spaces'
        (directory / 'sdd-plan-slices').mkdir(parents=True)
        (directory / 'sdd-plan-slices/SKILL.md').write_text('# Skill')
        self.runtime = directory
        self.assertEqual(self.command(f'cd "{directory}" && head -40 sdd-plan-slices/SKILL.md'),
                         ['sdd-plan-slices'])

    def test_absolute_read_and_bash_marker(self):
        marker = self.runtime / 'sdd-plan-slices' / 'SKILL.md'
        parsed = {'reads': [{'tool': 'read', 'path': str(marker)},
                            {'tool': 'bash', 'path': 'runtime/sdd-implement-slice/'}],
                  'skill_events': []}
        fired = events.detect_skills(parsed, self.runtime)
        self.assertEqual(fired, ['sdd-implement-slice', 'sdd-plan-slices'])

    def test_relative_read_against_project_cwd(self):
        parsed = {'reads': [{'tool': 'read', 'path': '../runtime/sdd-code-review/SKILL.md'}],
                  'skill_events': []}
        self.assertEqual(events.detect_skills(parsed, self.runtime, self.project),
                         ['sdd-code-review'])

    def test_skill_event_requires_exact_name(self):
        listing = '可用 skills: sdd-plan-slices, sdd-implement-slice, ...'
        parsed = {'reads': [], 'skill_events': [{'type': 'skill_list', 'key': 'skills',
                                                 'value': listing}]}
        self.assertEqual(events.detect_skills(parsed, self.runtime), [])
        parsed = {'reads': [], 'skill_events': [{'type': 'skill_start', 'key': 'skill',
                                                 'value': 'sdd-plan-slices'}]}
        self.assertEqual(events.detect_skills(parsed, self.runtime), ['sdd-plan-slices'])

    def test_single_skill_listing_is_not_activation(self):
        parsed = {'reads': [], 'skill_events': [
            {'type': 'skill_list', 'key': 'skill', 'value': 'sdd-plan-slices'}]}
        self.assertEqual(events.detect_skills(parsed, self.runtime), [])

    def test_outside_reads_do_not_fire(self):
        parsed = {'reads': [{'tool': 'read', 'path': 'src/app.py'}], 'skill_events': []}
        self.assertEqual(events.detect_skills(parsed, self.runtime, self.project), [])


if __name__ == '__main__':
    unittest.main()
