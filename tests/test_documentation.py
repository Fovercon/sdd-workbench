"""Check shipping navigation rather than depending on a developer's extra files."""
from pathlib import Path
import sys, unittest
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT/'tools'))
import docs, package

class DocumentationTests(unittest.TestCase):
    def test_shipped_markdown_links_and_long_references(self):
        result=docs.check(package.bundle_files(ROOT))
        self.assertEqual(result['errors'],[])
        self.assertGreater(result['local_links'],100)
    def test_missing_file_and_wrong_anchor_fail(self):
        result=docs.check({'README.md':b'[bad](missing.md) [bad](guide.md#wrong)', 'guide.md':b'# Guide\n'})
        self.assertEqual(len(result['errors']),2)
    def test_code_examples_are_not_real_links_and_duplicate_headings_resolve(self):
        data={'README.md':b'```md\n[fake](missing.md)\n```\n[go](guide.md#repeat-1)\n', 'guide.md':b'# Repeat\n## Repeat\n'}
        self.assertEqual(docs.check(data)['errors'],[])
    def test_escaped_outside_and_absolute_paths_fail(self):
        self.assertEqual(len(docs.check({'README.md':b'[x](../outside.md) [y](/etc/passwd)'})['errors']),2)
    def test_large_reference_requires_toc_and_unicode_anchor_resolves(self):
        key='skills/sdd-test/references/model.md'; text='# Model\n'+'text\n'*101
        self.assertTrue(docs.check({key:text.encode()})['errors'])
        data={'README.md':'[说明](guide.md#中文标题)'.encode(), 'guide.md':'# 中文标题'.encode()}
        self.assertEqual(docs.check(data)['errors'],[])
