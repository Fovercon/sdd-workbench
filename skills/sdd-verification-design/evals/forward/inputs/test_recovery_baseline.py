"""The original small safety net; deliberately not a held-out recovery oracle."""
from pathlib import Path
import tempfile
import unittest
from app import Ledger, filtered


class Baseline(unittest.TestCase):
    def test_existing_record_and_append(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)/'state.json'
            state.write_text('{"records":[{"id":"kept-1","date":"2026-01-10"}]}')
            ledger = Ledger(state)
            self.assertEqual(ledger.records()[0]['id'], 'kept-1')
            ledger.append({'id':'added-2','date':'2026-02-20'})
            self.assertEqual([row['id'] for row in Ledger(state).records()], ['kept-1','added-2'])

    def test_reversed_range_is_rejected(self):
        with self.assertRaises(ValueError): filtered([], '2026-02-01', '2026-01-01')

    def test_non_object_append_rejected_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)/'state.json'; state.write_text('{"records":[]}')
            before = state.read_bytes()
            for value in ([], None, 'label', 1):
                with self.assertRaises(ValueError): Ledger(state).append(value)
                self.assertEqual(state.read_bytes(), before)


if __name__ == '__main__': unittest.main()
