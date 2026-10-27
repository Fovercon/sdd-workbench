import unittest
from presentation import audit_label, export_row, sum_counts


class PresentationTests(unittest.TestCase):
    def test_export_v1(self):  # TC-EXPORT: C-001 v1
        self.assertEqual(export_row('12345678'), {'identifier': '****5678'})

    def test_audit_v1(self):  # TC-AUDIT: C-001 v1
        self.assertEqual(audit_label('12345678'), 'audit:****5678')

    def test_counts(self):  # TC-COUNT: FR-003 / AC-003
        values = [2, 0, 5]
        self.assertEqual(sum_counts(values), 7)
        self.assertEqual(sum_counts([]), 0)
        self.assertEqual(values, [2, 0, 5])
