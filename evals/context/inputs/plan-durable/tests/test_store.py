from pathlib import Path
import tempfile
import unittest
from store import enqueue, list_jobs


class StoreTests(unittest.TestCase):
    def test_sequential_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'jobs.json'
            record=enqueue(path, 'A', 'work')
            self.assertEqual(record, {'id':'A', 'payload':'work'})
            self.assertEqual(list_jobs(path), [record])
