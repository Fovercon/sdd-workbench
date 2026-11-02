from pathlib import Path
import tempfile
import unittest

from intake import intake, RejectedRecord


class IntakeTests(unittest.TestCase):
    def test_normal_file_bytes_and_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)/'out'
            records = [{'name':'b.txt','kind':'file','data':b'b'},
                       {'name':'a.txt','kind':'file','data':b'a'}]
            self.assertEqual(intake(records,root),['b.txt','a.txt'])
            self.assertEqual((root/'a.txt').read_bytes(),b'a')
            self.assertEqual((root/'b.txt').read_bytes(),b'b')

    def test_known_link_rejected_before_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)/'out'
            with self.assertRaises(RejectedRecord):
                intake([{'name':'link.txt','kind':'link','data':b'target'}],root)
            self.assertFalse(root.exists())

    def test_ignored_name_and_directory_do_not_become_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)/'out'
            records = [{'name':'~note.txt','kind':'future','data':b'ignored'},
                       {'name':'folder.txt','kind':'dir','data':b''}]
            self.assertEqual(intake(records,root),[])
            self.assertEqual(list(root.iterdir()),[])
