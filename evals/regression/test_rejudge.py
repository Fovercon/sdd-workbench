import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


class TestRejudge(unittest.TestCase):
    def test_uses_frozen_cases_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / 'source', root / 'derived'
            trial = source / 'l1' / 'case-1'
            trial.mkdir(parents=True)
            runtime = source / 'runtime-full' / 'sdd-workflow-router'
            runtime.mkdir(parents=True)
            (runtime / 'SKILL.md').write_text('# router')
            (source / 'manifest.json').write_text(json.dumps({'run_id': 'source'}))
            case = {'id': 'case-1', 'category': 'normal', 'prompt': '固定的历史提示',
                    'expect': {'trigger': ['sdd-workflow-router']}}
            (source / 'slots.json').write_text(json.dumps({'slots': [
                {'kind': 'l1', 'case': case}]}))
            (trial / 'events.jsonl').write_text('\n'.join(json.dumps(e) for e in [
                {'type': 'message_end', 'message': {'role': 'assistant', 'content': [
                    {'type': 'toolCall', 'id': 'c', 'name': 'bash', 'arguments': {
                        'command': f'cd {runtime} && cat SKILL.md'}}]}},
                {'type': 'tool_execution_end', 'toolCallId': 'c', 'isError': False},
                {'type': 'message_end', 'message': {'role': 'assistant', 'content': [
                    {'type': 'text', 'text': 'NEXT_STEP_READY'}]}},
            ]))
            (trial / 'result.json').write_text('{"correct":false,"exit_code":0}')
            before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in source.rglob('*') if p.is_file()}
            spec = importlib.util.spec_from_file_location('rejudge',
                            Path(__file__).parent / 'rejudge.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            report = module.rejudge(source, output)
            self.assertEqual(report['l1']['aggregate']['n_correct'], 1)
            self.assertTrue((output / 'report.md').is_file())
            self.assertEqual(before, {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in source.rglob('*') if p.is_file()})
            with self.assertRaises(FileExistsError):
                module.rejudge(source, output)
            manifest = json.loads((source / 'manifest.json').read_text())
            manifest['snapshot_hash'] = 'wrong-runtime'
            (source / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'runtime'):
                module.rejudge(source, root / 'mismatched')
            self.assertFalse((root / 'mismatched').exists())

    def test_case_id_cannot_escape_derived_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            (source / 'runtime-full').mkdir(parents=True)
            (source / 'manifest.json').write_text('{"run_id":"source"}')
            (source / 'slots.json').write_text(json.dumps({'slots': [
                {'kind': 'l1', 'case': {'id': '../../escape'}}]}))
            spec = importlib.util.spec_from_file_location('rejudge',
                            Path(__file__).parent / 'rejudge.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            with self.assertRaisesRegex(ValueError, 'case id'):
                module.rejudge(source, root / 'derived')
            self.assertFalse((root / 'derived').exists())
