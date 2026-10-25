import unittest
from service import select

class SelectionTests(unittest.TestCase):
    def test_existing_simple_match(self):
        self.assertEqual(select([{'id':'A'},{'id':'B'}], 'A'), [{'id':'A'}])

if __name__ == '__main__': unittest.main()
