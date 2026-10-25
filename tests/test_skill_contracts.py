"""Cross-artifact vocabularies; these checks do not evaluate Agent behavior."""
import ast
from pathlib import Path
import re
import unittest


SKILLS = Path(__file__).resolve().parents[1] / 'skills'


class SkillContracts(unittest.TestCase):
    def read(self, name, path):
        return (SKILLS / name / path).read_text(encoding='utf-8')

    def test_spec_template_and_summary_preserve_all_contract_states(self):
        model = self.read('sdd-requirements-contract', 'references/contract-model.md')
        states = set(re.findall(r'^\| `([A-Z_]+)` \|', model.split('## 2.')[0], re.M))
        template = self.read('sdd-requirements-contract', 'references/artifact-template.md')
        declarations = re.findall(r'^Status: (.+)$', template, re.M)
        self.assertEqual(len(declarations), 2)
        for declaration in declarations:
            with self.subTest(declaration=declaration):
                self.assertEqual(set(declaration.split(' | ')), states)

    def test_plan_template_preserves_executable_authority_bases(self):
        template = self.read('sdd-plan-slices', 'references/artifact-templates.md')
        declaration = re.search(r'^Status: (.+)$', template, re.M).group(1)
        self.assertEqual(set(declaration.split(' | ')),
                         {'READY_FOR_DESIGN_REVIEW', 'NEEDS_DECISION', 'APPROVED', 'DELEGATED_TECHNICAL'})

    def test_finish_targets_match_checkpoint_and_report(self):
        # Extract the real accepted target vocabulary, rather than maintaining a
        # second copy that could silently drift along with one template.
        script = self.read('sdd-workflow-router', 'scripts/sdd_loop.py')
        targets = next(set(ast.literal_eval(node)) for node in ast.walk(ast.parse(script))
                       if isinstance(node, ast.Set) and all(isinstance(x, ast.Constant) for x in node.elts)
                       and any(x.value == 'LOCAL' for x in node.elts))
        entry = self.read('sdd-finish-readiness', 'SKILL.md')
        section = entry.split('## Select the Finish target')[1].split('## Workflow')[0]
        self.assertEqual(set(re.findall(r'^- `([A-Z]+)`:', section, re.M)), targets)
        model = self.read('sdd-finish-readiness', 'references/readiness-model.md')
        profiles = model.split('## 2. Target profiles')[1].split('## 3.')[0]
        self.assertEqual(set(re.findall(r'^\| `([A-Z]+)` \|', profiles, re.M)), targets)
        report = self.read('sdd-finish-readiness', 'references/artifact-template.md')
        self.assertEqual(set(re.search(r'^targets: \[([^]]+)\]', report, re.M).group(1).split(', ')), targets)


if __name__ == '__main__':
    unittest.main()
