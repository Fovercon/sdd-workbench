import os
import subprocess
import sys
import tempfile
import unittest

from diff import render, tokenize, word_diff


class TestTokenize(unittest.TestCase):
    def test_splits_any_whitespace(self):
        self.assertEqual(tokenize('a  b\tc\n\nd'), ['a', 'b', 'c', 'd'])

    def test_empty(self):
        self.assertEqual(tokenize('   '), [])


class TestWordDiff(unittest.TestCase):
    def test_identical(self):
        self.assertEqual(word_diff('a b c', 'a b c'),
                         [('=', 'a'), ('=', 'b'), ('=', 'c')])

    def test_replace_deletions_first(self):
        self.assertEqual(word_diff('a b c', 'a x c'),
                         [('=', 'a'), ('-', 'b'), ('+', 'x'), ('=', 'c')])

    def test_insert_only(self):
        self.assertEqual(word_diff('a c', 'a b c'),
                         [('=', 'a'), ('+', 'b'), ('=', 'c')])

    def test_delete_only(self):
        self.assertEqual(word_diff('a b c', 'a c'),
                         [('=', 'a'), ('-', 'b'), ('=', 'c')])

    def test_ignore_case_compares_keeps_original(self):
        ops = word_diff('Hello world', 'hello world', ignore_case=True)
        self.assertEqual(ops, [('=', 'Hello'), ('=', 'world')])

    def test_ignore_case_off_by_default(self):
        ops = word_diff('Hello', 'hello')
        self.assertEqual(ops, [('-', 'Hello'), ('+', 'hello')])


class TestRender(unittest.TestCase):
    def test_prefixes(self):
        text = render([('=', 'a'), ('-', 'b'), ('+', 'c')])
        self.assertEqual(text, '  a\n- b\n+ c')

    def test_empty(self):
        self.assertEqual(render([]), '')


class TestCli(unittest.TestCase):
    def run_cli(self, old, new, *flags):
        paths = []
        for text in (old, new):
            fd, path = tempfile.mkstemp(suffix='.txt')
            with os.fdopen(fd, 'w', encoding='utf-8') as fh:
                fh.write(text)
            paths.append(path)
            self.addCleanup(os.unlink, path)
        return subprocess.run([sys.executable, 'diff.py', *flags, *paths],
                              capture_output=True, text=True, timeout=60)

    def test_exit_zero_when_equal(self):
        proc = self.run_cli('a b', 'a b')
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, '  a\n  b\n')

    def test_exit_one_when_different(self):
        proc = self.run_cli('a b', 'a c')
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, '  a\n- b\n+ c\n')

    def test_ignore_case_flag(self):
        proc = self.run_cli('A b', 'a b', '--ignore-case')
        self.assertEqual(proc.returncode, 0)

    def test_unreadable_exit_two(self):
        proc = subprocess.run([sys.executable, 'diff.py', 'nope1.txt', 'nope2.txt'],
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 2)
        self.assertIn('ERROR unreadable', proc.stderr)

    def test_empty_stdout(self):
        proc = self.run_cli('', '')
        self.assertEqual((proc.returncode, proc.stdout), (0, ''))
