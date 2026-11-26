"""Runtime freeze/subset/hash self-tests (worktree mode; no git writes)."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from runner import runtime  # noqa: E402
from runner.paths import suite_skills  # noqa: E402

FORBIDDEN_PARTS = {'evals', 'tests', '__pycache__'}


class TestFreeze(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dest = Path(self.tmp.name) / 'runtime'

    def test_freeze_contains_all_skills_only_runtime_parts(self):
        runtime.freeze(self.dest)
        frozen = sorted(p.name for p in self.dest.iterdir())
        self.assertEqual(frozen, sorted(suite_skills()))
        for path in self.dest.rglob('*'):
            if path.is_dir():
                continue
            rel = path.relative_to(self.dest).parts
            rest = rel[1:]
            self.assertTrue(rest == ('SKILL.md',) or rest[0] in runtime.RUNTIME_PARTS,
                            f'unexpected frozen path: {path}')
            self.assertNotIn('__pycache__', rel)
            self.assertNotIn('evals', rel)
            self.assertNotIn('tests', rel)

    def test_freeze_refuses_existing(self):
        runtime.freeze(self.dest)
        with self.assertRaises(ValueError):
            runtime.freeze(self.dest)

    def test_freeze_subset_names(self):
        names = suite_skills()[:2]
        runtime.freeze(self.dest, names=names)
        self.assertEqual(sorted(p.name for p in self.dest.iterdir()), sorted(names))

    def test_snapshot_hash_stable_and_sensitive(self):
        runtime.freeze(self.dest)
        first = runtime.snapshot_hash(self.dest)
        again = runtime.snapshot_hash(self.dest)
        self.assertEqual(first, again)
        target = next(self.dest.rglob('SKILL.md'))
        target.write_text(target.read_text(encoding='utf-8') + '\n<!-- touched -->',
                          encoding='utf-8')
        self.assertNotEqual(runtime.snapshot_hash(self.dest)['total'], first['total'])


class TestSubsetAndConditions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name) / 'full'
        runtime.freeze(self.source)

    def test_subset_and_refusal(self):
        names = suite_skills()[:3]
        dest = Path(self.tmp.name) / 'subset'
        runtime.subset(self.source, dest, names)
        self.assertEqual(sorted(p.name for p in dest.iterdir()), sorted(names))
        with self.assertRaises(ValueError):
            runtime.subset(self.source, Path(self.tmp.name) / 'subset', names)

    def test_subset_missing_skill_raises(self):
        with self.assertRaises(ValueError):
            runtime.subset(self.source, Path(self.tmp.name) / 'bad', ['sdd-no-such-skill'])

    def test_resolve_condition_specs(self):
        all_names = suite_skills()
        self.assertEqual(runtime.resolve_condition(['ALL'], all_names), all_names)
        no_router = runtime.resolve_condition(['ALL_MINUS', 'sdd-workflow-router'], all_names)
        self.assertNotIn('sdd-workflow-router', no_router)
        self.assertEqual(len(no_router), len(all_names) - 1)
        self.assertEqual(runtime.resolve_condition(['a', 'b'], all_names), ['a', 'b'])


if __name__ == '__main__':
    unittest.main()
