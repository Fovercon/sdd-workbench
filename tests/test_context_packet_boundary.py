"""A directory redirect must not let an excerpt escape its project root."""
from contextlib import nullcontext
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/sdd-workflow-router/scripts/context_packet.py'
spec = importlib.util.spec_from_file_location('packet_boundary', SCRIPT)
packet = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packet)


class ContextPacketBoundaryTests(unittest.TestCase):
    def redirect(self, link, target):
        if os.name == 'nt':
            run = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(target)], capture_output=True)
            self.assertEqual(run.returncode, 0, repr(run.stderr))
            self.addCleanup(lambda: link.rmdir() if link.exists() else None)
            return nullcontext()
        link.symlink_to(target, target_is_directory=True)
        # Windows junctions are directory redirects but is_symlink() is false.
        return mock.patch.object(Path, 'is_symlink', return_value=False)

    def test_redirect_outside_project_is_rejected_before_packet_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); project = root/'project'; project.mkdir()
            outside = root/'outside'; outside.mkdir(); (outside/'source.txt').write_bytes(b'outside\n')
            selection = {'schema': 1, 'task': 'selected source', 'sources': [
                {'id': 'source', 'path': 'linked/source.txt', 'start': 1, 'end': 1, 'reason': 'explicit'}]}
            link = project/'linked'
            with self.redirect(link, outside):
                with self.assertRaises(ValueError):
                    packet.build(project, selection, root/'packet')
                self.assertFalse((root/'packet').exists())
            if os.name == 'nt':
                link.rmdir()

    def test_source_replaced_by_outside_redirect_is_stale_even_with_same_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); project = root/'project'; project.mkdir()
            link = project/'linked'; link.mkdir(); (link/'source.txt').write_bytes(b'same\n')
            outside = root/'outside'; outside.mkdir(); (outside/'source.txt').write_bytes(b'same\n')
            selection = {'schema': 1, 'task': 'selected source', 'sources': [
                {'id': 'source', 'path': 'linked/source.txt', 'start': 1, 'end': 1, 'reason': 'explicit'}]}
            packet.build(project, selection, root/'packet')
            before = {p.name: p.read_bytes() for p in (root/'packet').iterdir()}
            (link/'source.txt').unlink(); link.rmdir()
            with self.redirect(link, outside):
                result = packet.check(project, root/'packet')
                self.assertEqual(result['status'], 'STALE')
                self.assertEqual(result['stale_ids'], ['source'])
                self.assertEqual(before, {p.name: p.read_bytes() for p in (root/'packet').iterdir()})
            if os.name == 'nt':
                link.rmdir()


if __name__ == '__main__':
    unittest.main()
