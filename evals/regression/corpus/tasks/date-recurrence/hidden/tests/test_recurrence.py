import unittest
from datetime import date

from recurrence import expand, parse_spec


class TestParseSpec(unittest.TestCase):
    def test_daily(self):
        self.assertEqual(parse_spec('daily'), {'kind': 'daily'})

    def test_daily_with_whitespace(self):
        self.assertEqual(parse_spec('  daily\n'), {'kind': 'daily'})

    def test_weekly(self):
        self.assertEqual(parse_spec('weekly:MON,WED'), {'kind': 'weekly', 'days': [0, 2]})

    def test_weekly_case_insensitive_dedupe(self):
        self.assertEqual(parse_spec('weekly:wed,WED,fri'), {'kind': 'weekly', 'days': [2, 4]})

    def test_interval(self):
        self.assertEqual(parse_spec('every:3d'), {'kind': 'interval', 'step': 3})

    def test_errors(self):
        for bad in ('hourly', 'weekly:', 'weekly:MON,X', 'every:0d', 'every:-2d',
                    'daily:extra', 'every:3m'):
            with self.assertRaises(ValueError, msg=bad):
                parse_spec(bad)


class TestExpand(unittest.TestCase):
    def test_daily_range(self):
        out = expand('daily', date(2026, 10, 1), date(2026, 10, 4))
        self.assertEqual([d.day for d in out], [1, 2, 3])  # end excluded by default

    def test_daily_include_end(self):
        out = expand('daily', date(2026, 10, 1), date(2026, 10, 4), include_end=True)
        self.assertEqual([d.day for d in out], [1, 2, 3, 4])

    def test_daily_exclude_start(self):
        out = expand('daily', date(2026, 10, 1), date(2026, 10, 3), include_start=False)
        self.assertEqual([d.day for d in out], [2])

    def test_weekly_multi_day(self):
        out = expand('weekly:MON,FRI', date(2026, 10, 1), date(2026, 10, 19))
        self.assertEqual(out, [date(2026, 10, 2), date(2026, 10, 5), date(2026, 10, 9),
                               date(2026, 10, 12), date(2026, 10, 16)])

    def test_interval_every_three(self):
        out = expand('every:3d', date(2026, 10, 1), date(2026, 10, 10))
        self.assertEqual(out, [date(2026, 10, 1), date(2026, 10, 4), date(2026, 10, 7)])

    def test_start_after_end(self):
        self.assertEqual(expand('daily', date(2026, 10, 5), date(2026, 10, 1)), [])

    def test_single_day_window(self):
        self.assertEqual(expand('daily', date(2026, 10, 1), date(2026, 10, 1)), [])
        self.assertEqual(expand('daily', date(2026, 10, 1), date(2026, 10, 1),
                                include_end=True), [date(2026, 10, 1)])

    def test_invalid_spec_propagates(self):
        with self.assertRaises(ValueError):
            expand('weekly:XYZ', date(2026, 10, 1), date(2026, 10, 5))
