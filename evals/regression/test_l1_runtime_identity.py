"""Executing read-only Python helpers must not invalidate frozen L1 source identity."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runner import runtime


class TestRuntimeIdentity(unittest.TestCase):
    def test_generated_bytecode_is_not_a_source_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / 'sdd-project-bootstrap'
            skill.mkdir()
            source = skill / 'SKILL.md'
            source.write_text('# Baseline')
            original = runtime.snapshot_hash(root)
            cache = skill / '__pycache__'
            cache.mkdir()
            (cache / 'helper.cpython-312.pyc').write_bytes(b'generated')
            self.assertEqual(runtime.snapshot_hash(root), original)
            source.write_text('# Changed rule')
            self.assertNotEqual(runtime.snapshot_hash(root), original)
