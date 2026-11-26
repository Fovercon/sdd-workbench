import json
import unittest

from checklist import from_json, parse, stats, to_json


class TestParse(unittest.TestCase):
    def test_mixed_states(self):
        parsed = parse('# 标题\n- [ ] 买牛奶\n- [x] 交报告\n- [X] 复核\n正文')
        self.assertEqual(parsed['items'], [
            {'text': '买牛奶', 'done': False},
            {'text': '交报告', 'done': True},
            {'text': '复核', 'done': True}])
        self.assertEqual(parsed['invalid_lines'], 0)

    def test_indentation_and_spacing(self):
        parsed = parse('   - [ ]  缩进项')
        self.assertEqual(parsed['items'], [{'text': '缩进项', 'done': False}])

    def test_empty_text_is_legal(self):
        parsed = parse('- [ ]')
        self.assertEqual(parsed['items'], [{'text': '', 'done': False}])

    def test_invalid_prefix_lines_counted(self):
        parsed = parse('- [x 残缺\n- [y] 不是勾选\n- [ ] 正常\n普通行')
        self.assertEqual(parsed['invalid_lines'], 2)
        self.assertEqual(len(parsed['items']), 1)

    def test_dedupe_keeps_first(self):
        parsed = parse('- [x] 同名\n- [ ] 同名\n- [x] 同名')
        self.assertEqual(parsed['items'], [{'text': '同名', 'done': True}])

    def test_headers_blank_plain_ignored(self):
        parsed = parse('## 二级\n\n就是一句普通的话\n1. 不是清单')
        self.assertEqual(parsed, {'items': [], 'invalid_lines': 0})


class TestRoundtrip(unittest.TestCase):
    def test_to_json_format(self):
        text = to_json({'items': [{'text': '中', 'done': True}], 'invalid_lines': 0})
        self.assertEqual(text, '{\n  "items": [\n    {\n      "text": "中",\n'
                               '      "done": true\n    }\n  ],\n  "invalid_lines": 0\n}')

    def test_roundtrip(self):
        parsed = parse('- [ ] a\n- [x] b\n- [bad')
        self.assertEqual(from_json(to_json(parsed)), parsed)

    def test_from_json_bad_input_raises_value_error(self):
        with self.assertRaises(ValueError):
            from_json('not json')


class TestStats(unittest.TestCase):
    def test_counts(self):
        parsed = parse('- [x] a\n- [ ] b\n- [ ] c')
        self.assertEqual(stats(parsed), {'total': 3, 'done': 1, 'open': 2})

    def test_empty(self):
        self.assertEqual(stats({'items': [], 'invalid_lines': 0}),
                         {'total': 0, 'done': 0, 'open': 0})
