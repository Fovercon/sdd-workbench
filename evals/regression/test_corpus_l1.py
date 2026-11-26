"""L1 corpus self-tests: schema, coverage classes, fixture existence, and that the
outcome-enum map stays in sync with the actual SKILL.md files."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from runner import l1_trigger  # noqa: E402
from runner.paths import CORPUS  # noqa: E402


class TestCorpusSchema(unittest.TestCase):
    def setUp(self):
        self.cases = l1_trigger.load_cases()

    def test_corpus_size(self):
        self.assertGreaterEqual(len(self.cases), 60, 'corpus should stay at ~70 cases')

    def test_ids_unique_and_prefixes(self):
        ids = [c['id'] for c in self.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_coverage_classes_present(self):
        categories = {c['category'] for c in self.cases}
        for needed in ('normal', 'confusion', 'negative', 'boundary', 'over-process'):
            self.assertIn(needed, categories, f'missing category {needed}')

    def test_negatives_expect_no_skill(self):
        for case in self.cases:
            if case['category'] == 'negative':
                self.assertEqual(case['expect']['trigger'], [])

    def test_prompts_never_name_skills(self):
        for case in self.cases:
            for name in l1_trigger.OUTCOME_ENUMS:
                self.assertNotIn(name, case['prompt'], f"{case['id']} names a skill")

    def test_every_skill_has_positive_case(self):
        covered = set()
        for case in self.cases:
            covered.update(case['expect']['trigger'])
        for skill in l1_trigger.OUTCOME_ENUMS:
            self.assertIn(skill, covered, f'{skill} has no positive case')


class TestOutcomeEnumSync(unittest.TestCase):
    def test_enum_tokens_exist_in_skill_md(self):
        for skill, tokens in l1_trigger.OUTCOME_ENUMS.items():
            body = (ROOT / 'skills' / skill / 'SKILL.md').read_text(encoding='utf-8')
            for token in tokens:
                self.assertIn(token, body, f'{skill}: token {token} missing from SKILL.md')


class TestFixtures(unittest.TestCase):
    def test_bounded_edit_has_a_real_target(self):
        case = next(c for c in l1_trigger.load_cases() if c['id'] == 'impl-bounded-0003')
        root = CORPUS / 'l1' / 'fixtures' / case['fixture']
        code = '\n'.join(p.read_text(encoding='utf-8') for p in root.rglob('*.py'))
        self.assertIn('¥', code)

    def test_small_readme_edit_requires_no_router_and_has_target(self):
        case = next(c for c in l1_trigger.load_cases() if c['id'] == 'router-no-ceremony-0006')
        self.assertEqual(case['expect']['trigger'], [])
        root = CORPUS / 'l1' / 'fixtures' / case['fixture']
        self.assertIn('demo', (root / 'README.md').read_text(encoding='utf-8'))

    def test_view_outcomes_are_not_scored_as_diagnostics(self):
        for name in ('router-view-0005', 'router-human-gate-0007'):
            case = next(c for c in l1_trigger.load_cases() if c['id'] == name)
            self.assertFalse(case.get('enum_required', True))

    def test_fixtures_exist_for_every_case(self):
        for case in l1_trigger.load_cases():
            if case.get('fixture'):
                self.assertTrue((CORPUS / 'l1' / 'fixtures' / case['fixture']).is_dir(),
                                f"{case['id']}: fixture {case['fixture']} missing")


if __name__ == '__main__':
    unittest.main()
