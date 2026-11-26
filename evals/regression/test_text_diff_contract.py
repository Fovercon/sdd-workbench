"""The public render API and CLI have independent newline contracts."""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORACLE = HERE / 'corpus/tasks/text-diff/oracle/solution/diff.py'


class TestTextDiffContract(unittest.TestCase):
    def test_render_has_no_trailing_newline_and_empty_render_is_empty(self):
        spec = importlib.util.spec_from_file_location('contract_diff', ORACLE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.render([('=', 'a'), ('-', 'b'), ('+', 'c')]),
                         '  a\n- b\n+ c')
        self.assertEqual(module.render([]), '')

    def test_cli_keeps_one_trailing_newline_for_nonempty_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = Path(tmp) / 'old', Path(tmp) / 'new'
            old.write_text('a b', encoding='utf-8')
            new.write_text('a c', encoding='utf-8')
            proc = subprocess.run([sys.executable, '-B', str(ORACLE), str(old), str(new)],
                                  capture_output=True, text=True, timeout=30)
            self.assertEqual((proc.returncode, proc.stdout, proc.stderr),
                             (1, '  a\n- b\n+ c\n', ''))
            old.write_text('', encoding='utf-8')
            new.write_text('', encoding='utf-8')
            proc = subprocess.run([sys.executable, '-B', str(ORACLE), str(old), str(new)],
                                  capture_output=True, text=True, timeout=30)
            self.assertEqual((proc.returncode, proc.stdout, proc.stderr), (0, '', ''))


if __name__ == '__main__':
    unittest.main()
