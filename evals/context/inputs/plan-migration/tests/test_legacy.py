from pathlib import Path
import unittest
from legacy import batch_rows, web_rows

ROOT = Path(__file__).resolve().parents[1]


class LegacyCharacterization(unittest.TestCase):
    def test_web_preserves_spaces_and_conversion_meaning(self):
        self.assertEqual(web_rows(ROOT/'data/web.json')[0],
                         {'id': '7', 'label': 'web:7', 'text': '  Alpha  ',
                          'state': 'done', 'meaning': 'converted'})

    def test_batch_strips_display_and_preserves_delivery_meaning(self):
        self.assertEqual(batch_rows(ROOT/'data/batch.json')[0],
                         {'id': '7', 'label': 'batch:7', 'text': 'Beta',
                          'state': 'done', 'meaning': 'delivered'})

    def test_same_local_id_is_not_same_origin_or_claim(self):
        web = web_rows(ROOT/'data/web.json')[0]
        batch = batch_rows(ROOT/'data/batch.json')[0]
        self.assertEqual(web['id'], batch['id'])
        self.assertNotEqual(web['label'], batch['label'])
        self.assertNotEqual(web['meaning'], batch['meaning'])

    def test_order_and_source_bytes_preserved(self):
        for name, read, expected in [('web', web_rows, ['7', 'w2']),
                                     ('batch', batch_rows, ['7', 'b2'])]:
            source = ROOT/'data'/f'{name}.json'; before = source.read_bytes()
            self.assertEqual([r['id'] for r in read(source)], expected)
            self.assertEqual(source.read_bytes(), before)
