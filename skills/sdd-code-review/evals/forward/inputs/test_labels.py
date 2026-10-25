import unittest
from labels import normalize_label, unique_labels


class Baseline(unittest.TestCase):
    def test_trim(self):
        self.assertEqual(normalize_label('  Hello  '), 'Hello')

    def test_two_different_labels(self):
        self.assertEqual(unique_labels(['One', 'Two']), ['One', 'Two'])


if __name__ == '__main__': unittest.main()
