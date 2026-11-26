import json
import os
import subprocess
import sys
import tempfile
import unittest

from report import parse_line, summarize


class TestParseLine(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(parse_line('2026-10-01,east,apple,120.5'),
                         ('2026-10-01', 'east', 'apple', 120.5))

    def test_strips_fields(self):
        self.assertEqual(parse_line(' 2026-10-01 , east , apple , 1 '),
                         ('2026-10-01', 'east', 'apple', 1.0))

    def test_blank_returns_none(self):
        self.assertIsNone(parse_line(''))
        self.assertIsNone(parse_line('   '))

    def test_wrong_column_count(self):
        self.assertIsNone(parse_line('a,b,c'))

    def test_bad_amount(self):
        self.assertIsNone(parse_line('d,r,p,NaNx'))

    def test_negative_amount_allowed(self):
        self.assertEqual(parse_line('d,r,p,-2.5')[3], -2.5)


class TestSummarize(unittest.TestCase):
    def test_sorted_by_region(self):
        rows = [('d', 'west', 'p', 1.0), ('d', 'east', 'p', 2.0), ('d', 'west', 'p', 3.0)]
        self.assertEqual(summarize(rows), [('east', 2.0), ('west', 4.0)])

    def test_empty(self):
        self.assertEqual(summarize([]), [])


class TestCli(unittest.TestCase):
    def run_cli(self, text=None, path=None):
        if path is None:
            fd, path = tempfile.mkstemp(suffix='.csv')
            with os.fdopen(fd, 'w', encoding='utf-8') as fh:
                fh.write(text)
            self.addCleanup(os.unlink, path)
        return subprocess.run([sys.executable, 'report.py', path],
                              capture_output=True, text=True, timeout=60)

    def test_output_lines_and_regions(self):
        proc = self.run_cli('2026-10-01,west,pear,80\n2026-10-02,east,apple,120.5\n'
                            '2026-10-03,west,fig,20.25\n')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, 'east\t120.50\nwest\t100.25\nREGIONS\t2\n')

    def test_bom_tolerated(self):
        proc = self.run_cli('﻿2026-10-01,east,apple,10\n')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, 'east\t10.00\nREGIONS\t1\n')

    def test_skipped_reported_on_stderr(self):
        proc = self.run_cli('bad,line\n2026-10-01,east,apple,10\n\n')
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stderr.strip(), 'SKIPPED\t2')
        self.assertEqual(proc.stdout, 'east\t10.00\nREGIONS\t1\n')

    def test_missing_file_exit_2(self):
        proc = self.run_cli(path='definitely-missing-8347.csv')
        self.assertEqual(proc.returncode, 2)
        self.assertIn('ERROR missing file', proc.stderr)

    def test_empty_file(self):
        proc = self.run_cli('')
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, 'REGIONS\t0\n')
