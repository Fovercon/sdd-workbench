"""The grader must preserve actor test paths and select only changed tests."""
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from runner import l2_e2e


class TestVisibleTestLayout(unittest.TestCase):
    def symlink(self, target, link):
        try:
            os.symlink(target, link)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f'symlink unavailable: {exc}')

    def slot(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        dest = root / 'l2' / 'synthetic' / 'baseline' / 't1'
        project = dest / 'project'
        project.mkdir(parents=True)
        (dest / 'events.jsonl').write_text('', encoding='utf-8')
        (dest / 'process-result.json').write_text('{"exit_code": 0}', encoding='utf-8')
        (dest / 'starter-manifest.json').write_text('{}', encoding='utf-8')
        task_root = root / 'task'
        task_root.mkdir()
        return dest, project, {'root': task_root, 'kind': 'code'}

    def check(self, dest, task):
        return l2_e2e.adjudicate(dest, {'id': 'baseline'}, task)['visible']

    def test_file_relative_cli_and_fixture_keep_project_layout(self):
        dest, project, task = self.slot()
        (project / 'answer.txt').write_text('correct', encoding='utf-8')
        (project / 'cli.py').write_text(
            "from pathlib import Path\nprint(Path(__file__).with_name('answer.txt').read_text())\n",
            encoding='utf-8')
        tests = project / 'tests'
        tests.mkdir()
        (tests / 'input.txt').write_text('correct', encoding='utf-8')
        (tests / 'test_cli.py').write_text(
            "import subprocess,sys,unittest\nfrom pathlib import Path\n"
            "ROOT=Path(__file__).resolve().parent.parent\n"
            "class CliTest(unittest.TestCase):\n"
            " def test_cli(self):\n"
            "  p=subprocess.run([sys.executable,str(ROOT/'cli.py')],capture_output=True,text=True)\n"
            "  self.assertEqual(p.returncode,0)\n"
            "  self.assertEqual(p.stdout,Path(__file__).with_name('input.txt').read_text()+'\\n')\n",
            encoding='utf-8')
        visible = self.check(dest, task)
        self.assertEqual((visible['passed'], visible['total']), (1, 1), visible)

    def test_same_basenames_in_different_directories_both_execute(self):
        dest, project, task = self.slot()
        for directory, name in [('unit', 'Unit'), ('integration', 'Integration')]:
            tests = project / 'tests' / directory
            tests.mkdir(parents=True)
            (tests / 'test_shared.py').write_text(
                f'import unittest\nclass {name}(unittest.TestCase):\n'
                ' def test_runs(self):self.assertTrue(True)\n', encoding='utf-8')
        visible = self.check(dest, task)
        self.assertEqual((visible['passed'], visible['total']), (2, 2), visible)

    def test_package_relative_helpers_still_import(self):
        dest, project, task = self.slot()
        tests = project / 'tests'
        tests.mkdir()
        (tests / '__init__.py').write_text('', encoding='utf-8')
        (tests / 'helper.py').write_text('VALUE = 42\n', encoding='utf-8')
        (tests / 'test_relative.py').write_text(
            'import unittest\nfrom .helper import VALUE\nclass Relative(unittest.TestCase):\n'
            ' def test_value(self):self.assertEqual(VALUE,42)\n', encoding='utf-8')
        visible = self.check(dest, task)
        self.assertEqual((visible['passed'], visible['total']), (1, 1), visible)

    def test_unchanged_starter_test_is_not_imported_or_executed(self):
        dest, project, task = self.slot()
        tests = project / 'tests'
        tests.mkdir()
        old = tests / 'test_starter.py'
        old.write_text("raise RuntimeError('unchanged test must not be imported')\n", encoding='utf-8')
        (dest / 'starter-manifest.json').write_text(json.dumps({
            'tests/test_starter.py': hashlib.sha256(old.read_bytes()).hexdigest()}), encoding='utf-8')
        (tests / 'test_new.py').write_text(
            'import unittest\nclass New(unittest.TestCase):\n'
            ' def test_runs(self):self.assertTrue(True)\n', encoding='utf-8')
        visible = self.check(dest, task)
        self.assertEqual((visible['passed'], visible['total']), (1, 1), visible)

    def test_visible_test_writes_do_not_mutate_actor_project(self):
        dest, project, task = self.slot()
        tests = project / 'tests'
        tests.mkdir()
        (tests / 'test_write.py').write_text(
            'import unittest\nfrom pathlib import Path\n'
            'class Writer(unittest.TestCase):\n'
            " def test_runs(self):Path('created-by-test.txt').write_text('temporary')\n",
            encoding='utf-8')
        visible = self.check(dest, task)
        self.assertEqual((visible['passed'], visible['total']), (1, 1), visible)
        self.assertFalse((project / 'created-by-test.txt').exists())

    def test_absolute_internal_symlink_targets_the_copy(self):
        dest, project, task = self.slot()
        state = project / 'state.txt'
        state.write_text('original', encoding='utf-8')
        self.symlink(str(state), project / 'alias')
        tests = project / 'tests'
        tests.mkdir()
        (tests / 'test_write.py').write_text(
            'import unittest\nfrom pathlib import Path\nclass Writer(unittest.TestCase):\n'
            " def test_runs(self):Path('alias').write_text('graded copy')\n", encoding='utf-8')
        visible = self.check(dest, task)
        self.assertEqual((visible['passed'],visible['total']), (1,1), visible)
        self.assertEqual(state.read_text(), 'original')

    def test_external_symlink_is_an_explicit_evaluator_error(self):
        dest, project, task = self.slot()
        outside = dest / 'outside.txt'
        outside.write_text('original', encoding='utf-8')
        self.symlink(str(outside), project / 'alias')
        tests = project / 'tests'
        tests.mkdir()
        (tests / 'test_new.py').write_text('import unittest\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'EVALUATOR_ERROR.*external'):
            self.check(dest, task)
        self.assertEqual(outside.read_text(), 'original')

    def test_circular_symlink_is_an_explicit_evaluator_error(self):
        dest, project, task = self.slot()
        self.symlink('alias', project / 'alias')
        tests = project / 'tests'
        tests.mkdir()
        (tests / 'test_new.py').write_text('import unittest\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'EVALUATOR_ERROR.*symlink'):
            self.check(dest, task)


if __name__ == '__main__':
    unittest.main()
