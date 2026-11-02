"""Exercise the public context CLI; identity checks must not imply approval."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CLI = Path(__file__).resolve().parents[1] / 'scripts/context_packet.py'


class ContextPacketTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.project = self.base / 'project'
        self.project.mkdir()
        (self.project / 'spec.md').write_bytes(
            'old history\r\nFR-7：仅重跑选中的失败项。\r\n成功结果内容保持不变。\r\n'.encode())
        (self.project / 'shared.md').write_text('All writes require the task lock.\n', encoding='utf-8')
        self.selection = {'schema': 1, 'task': '准备当前重跑切片', 'sources': [
            {'id': 'FR-7', 'path': 'spec.md', 'start': 2, 'end': 3,
             'reason': '当前行为及成功结果保护义务'},
            {'id': 'lock', 'path': 'shared.md', 'start': 1, 'end': 1,
             'reason': '共享写入约束'}]}
        self.packet = self.base / 'packet'
        self.original = self.snapshot()

    def snapshot(self):
        return {p.relative_to(self.project).as_posix(): p.read_bytes()
                for p in self.project.rglob('*') if p.is_file()}

    def cli(self, *args, encoding=None):
        env = {**os.environ}
        if encoding:
            env['PYTHONIOENCODING'] = encoding
        return subprocess.run([sys.executable, '-B', str(CLI), *map(str, args)],
                              capture_output=True, env=env)

    def build(self, selection=None, packet=None, limit=32768, encoding=None):
        path = self.base / 'selection.json'
        path.write_text(json.dumps(self.selection if selection is None else selection,
                                   ensure_ascii=False), encoding='utf-8')
        return self.cli('build', '--project', self.project, '--selection', path,
                        '--output', packet or self.packet, '--max-bytes', limit, encoding=encoding)

    def built(self):
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads((self.packet / 'receipt.json').read_text(encoding='utf-8'))

    def test_build_preserves_selected_utf8_lines_and_shared_constraint_without_history(self):
        receipt = self.built()
        context = (self.packet / 'context.md').read_bytes()
        self.assertIn('FR-7：仅重跑选中的失败项。\r\n成功结果内容保持不变。\r\n'.encode(), context)
        self.assertIn(b'All writes require the task lock.\n', context)
        self.assertNotIn(b'old history', context)
        self.assertEqual(receipt['context_bytes'], len(context))
        self.assertEqual(receipt['context_sha256'], hashlib.sha256(context).hexdigest())
        self.assertEqual(receipt['sources'][0]['sha256'],
                         hashlib.sha256((self.project / 'spec.md').read_bytes()).hexdigest())
        self.assertEqual(self.snapshot(), self.original)
        result = self.cli('check', self.packet, '--project', self.project)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'CURRENT')

    def test_unicode_separators_inside_a_physical_line_do_not_drop_contract_text(self):
        for n, separator in enumerate(('\u2028', '\u2029', '\x0b', '\x0c', '\x85')):
            with self.subTest(separator=repr(separator)):
                line = 'FR-1: preserve before' + separator + 'and after.\n'
                (self.project / 'spec.md').write_bytes((line + 'FR-2: next physical line.\r\n').encode())
                selection = copy.deepcopy(self.selection)
                selection['sources'][0].update(start=1, end=1)
                output = self.base / f'unicode-{n}'
                result = self.build(selection, output)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(line.encode(), (output / 'context.md').read_bytes())
                selection['sources'][0].update(start=2, end=2)
                output = self.base / f'next-line-{n}'
                self.assertEqual(self.build(selection, output).returncode, 0)
                self.assertIn(b'FR-2: next physical line.\r\n', (output / 'context.md').read_bytes())

    def test_change_outside_selected_lines_or_missing_source_withdraws_current(self):
        self.built()
        for missing in (False, True):
            with self.subTest(missing=missing):
                p = self.project / 'spec.md'
                if missing:
                    p.unlink()
                else:
                    p.write_bytes(self.original['spec.md'].replace(b'old history', b'changed history'))
                result = self.cli('check', self.packet, '--project', self.project)
                self.assertEqual(result.returncode, 1, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report['status'], 'STALE')
                self.assertEqual(report['stale_ids'], ['FR-7'])

    def test_tampered_body_or_invalid_receipt_is_an_error(self):
        self.built()
        body = self.packet / 'context.md'
        body.write_bytes(body.read_bytes() + b'Invented approval')
        self.assertEqual(self.cli('check', self.packet, '--project', self.project).returncode, 2)
        (self.packet / 'receipt.json').write_text('{}', encoding='utf-8')
        self.assertEqual(self.cli('check', self.packet, '--project', self.project).returncode, 2)

    def test_receipt_cannot_drop_a_source_or_relabel_the_task_without_changing_the_body(self):
        receipt = self.built()
        for field, replacement in [('sources', receipt['sources'][:1]), ('task', 'different task')]:
            with self.subTest(field=field):
                changed = copy.deepcopy(receipt)
                changed[field] = replacement
                (self.packet / 'receipt.json').write_text(json.dumps(changed), encoding='utf-8')
                result = self.cli('check', self.packet, '--project', self.project)
                self.assertEqual(result.returncode, 2)

    def test_same_content_in_different_project_is_not_the_same_workspace(self):
        self.built()
        other = self.base / 'other'
        other.mkdir()
        for name, data in self.original.items():
            (other / name).write_bytes(data)
        result = self.cli('check', self.packet, '--project', other)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['status'], 'FOREIGN_WORKSPACE')

    def test_byte_limit_is_exact_and_never_silently_truncates(self):
        receipt = self.built()
        size = receipt['context_bytes']
        result = self.build(packet=self.base / 'exact', limit=size)
        self.assertEqual(result.returncode, 0, result.stderr)
        rejected = self.base / 'too-small'
        result = self.build(packet=rejected, limit=size - 1)
        self.assertEqual(result.returncode, 2)
        self.assertIn(b'budget', result.stderr)
        self.assertFalse(rejected.exists())
        self.assertEqual(self.snapshot(), self.original)

    def test_existing_output_and_pinned_version_mismatch_do_not_write(self):
        self.packet.mkdir()
        sentinel = self.packet / 'keep.txt'
        sentinel.write_bytes(b'existing work')
        self.assertEqual(self.build().returncode, 2)
        self.assertEqual(list(self.packet.iterdir()), [sentinel])
        selection = copy.deepcopy(self.selection)
        selection['sources'][0]['expected_sha256'] = '0' * 64
        rejected = self.base / 'bad-version'
        result = self.build(selection, rejected)
        self.assertEqual(result.returncode, 2)
        self.assertIn(b'fingerprint', result.stderr)
        self.assertFalse(rejected.exists())
        self.assertEqual(self.snapshot(), self.original)

    def test_invalid_selection_ranges_identifiers_and_utf8_do_not_create_a_packet(self):
        cases = [[], {}, {'schema': 2, 'task': 'x', 'sources': []}]
        for field, value in [('start', 0), ('start', True), ('end', 99),
                             ('end', 1), ('reason', ''), ('expected_sha256', 'bad')]:
            selection = copy.deepcopy(self.selection)
            selection['sources'][0][field] = value
            cases.append(selection)
        duplicated = copy.deepcopy(self.selection)
        duplicated['sources'][1]['id'] = 'FR-7'
        cases.append(duplicated)
        for n, selection in enumerate(cases):
            with self.subTest(selection=selection):
                output = self.base / f'invalid-{n}'
                result = self.build(selection, output)
                self.assertEqual(result.returncode, 2)
                self.assertIn(b'error', result.stderr.lower())
                self.assertFalse(output.exists())
        (self.project / 'spec.md').write_bytes(b'\xff')
        result = self.build()
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.packet.exists())

    def test_absolute_parent_and_windows_paths_are_rejected(self):
        for n, path in enumerate(('../outside.txt', str(self.base / 'outside.txt'),
                                  'C:/outside.txt', '..\\outside.txt')):
            with self.subTest(path=path):
                selection = copy.deepcopy(self.selection)
                selection['sources'][0]['path'] = path
                output = self.base / f'escape-{n}'
                result = self.build(selection, output)
                self.assertEqual(result.returncode, 2)
                self.assertIn(b'path', result.stderr.lower())
                self.assertFalse(output.exists())

    def test_symlink_file_and_intermediate_directory_are_rejected(self):
        outside = self.base / 'outside'
        outside.mkdir()
        (outside / 'secret.txt').write_text('outside data\n', encoding='utf-8')
        try:
            (self.project / 'linked').symlink_to(outside, target_is_directory=True)
            (self.project / 'alias').symlink_to(outside / 'secret.txt')
        except OSError as error:
            self.skipTest(f'Symlinks unavailable: {error}')
        for n, path in enumerate(('linked/secret.txt', 'alias')):
            selection = copy.deepcopy(self.selection)
            selection['sources'][0].update(path=path, start=1, end=1)
            output = self.base / f'link-{n}'
            result = self.build(selection, output)
            self.assertEqual(result.returncode, 2)
            self.assertIn(b'symlink', result.stderr.lower())
            self.assertFalse(output.exists())

    def test_cli_json_survives_a_non_utf8_pipe(self):
        result = self.build(encoding='cp1252')
        self.assertEqual(result.returncode, 0, result.stderr)
        json.loads(result.stdout)
        result = self.cli('check', self.packet, '--project', self.project, encoding='cp1252')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'CURRENT')


if __name__ == '__main__':
    unittest.main()
