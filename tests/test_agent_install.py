"""Named-agent installation contracts, always under isolated home directories."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import package
from install import Installation, main, target_directories


class AgentInstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.home = self.base / 'home'
        self.source = self.base / 'source'
        for name, data in package.bundle_files(ROOT).items():
            path = self.source / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)

    def cli(self, *args):
        return subprocess.run([sys.executable, '-B', str(ROOT / 'tools/install.py'), *args,
                               '--home', str(self.home)], capture_output=True, text=True)

    def test_six_defaults_and_shared_target(self):
        targets = target_directories(['all', 'shared'], self.home)
        self.assertEqual({name: path.relative_to(self.home).as_posix() for name, path in targets.items()}, {
            'codex': '.codex/skills', 'hermes': '.hermes/skills', 'zcode': '.zcode/skills',
            'deepseek': '.dsh/skills', 'opencode': '.config/opencode/skills',
            'pi': '.pi/agent/skills', 'shared': '.agents/skills'})
        self.assertFalse(self.home.exists())

    def test_environment_overrides_and_explicit_home_isolation(self):
        env = {'CODEX_HOME': str(self.base/'cx'), 'HERMES_HOME': str(self.base/'hm'),
               'DSH_HOME': str(self.base/'ds'), 'XDG_CONFIG_HOME': str(self.base/'cfg'),
               'PI_CODING_AGENT_DIR': str(self.base/'pi')}
        targets = target_directories(['all'], environ=env)
        for name, key in [('codex','CODEX_HOME'),('hermes','HERMES_HOME'),('deepseek','DSH_HOME'),('pi','PI_CODING_AGENT_DIR')]:
            self.assertEqual(targets[name], Path(env[key])/'skills')
        self.assertEqual(targets['opencode'], Path(env['XDG_CONFIG_HOME'])/'opencode/skills')
        self.assertEqual(target_directories(['codex'], self.home, env)['codex'], self.home/'.codex/skills')

    def test_aliases_deduplicate_and_unknown_targets_fail(self):
        self.assertEqual(list(target_directories(['hermes-agent','hermes','dsh','deepseek-harness'],self.home)), ['hermes','deepseek'])
        for names in (['unknown'], ['all','unknown']):
            with self.assertRaisesRegex(ValueError, 'Unknown agent'):
                target_directories(names, self.home)

    def test_all_agents_install_identical_complete_skills_and_preserve_unmanaged(self):
        targets = target_directories(['all'], self.home)
        for path in targets.values():
            custom = path/'my-skill/SKILL.md'; custom.parent.mkdir(parents=True); custom.write_text('mine')
        result = self.cli('install','--source',str(self.source),'--agent','all')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(set(json.loads(result.stdout)['agents']),set(targets))
        skills = package.load(self.source/'suite.json')['skills']
        for name,dest in targets.items():
            self.assertEqual(Installation(dest).status()['changed'],[],name)
            self.assertEqual((dest/'my-skill/SKILL.md').read_text(),'mine')
            for skill in skills:
                self.assertEqual(package.tree_hashes(dest/skill),package.tree_hashes(self.source/'skills'/skill))

    def test_each_target_retains_upgrade_backup_and_rolls_back(self):
        self.assertEqual(self.cli('install','--source',str(self.source),'--agent','all').returncode,0)
        original = package.load(self.source/'plugin.json')['version']
        major,minor,patch=map(int,original.split('-')[0].split('.'))
        package.bump_version(f'{major}.{minor}.{patch+1}',self.source)
        with (self.source/'skills/sdd-code-review/SKILL.md').open('a') as f: f.write('\nFixture upgrade\n')
        result = self.cli('install','--source',str(self.source),'--agent','all')
        self.assertEqual(result.returncode,0,result.stderr)
        for record in json.loads(result.stdout)['agents'].values():
            self.assertTrue((Path(record['backup'])/'before/sdd-code-review/SKILL.md').is_file())
        self.assertEqual(self.cli('rollback','--agent','all').returncode,0)
        for dest in target_directories(['all'],self.home).values():
            self.assertEqual(Installation(dest).status()['version'],original)
            self.assertNotIn('Fixture upgrade',(dest/'sdd-code-review/SKILL.md').read_text())

    def test_known_conflict_blocks_all_targets_before_writes(self):
        dest = target_directories(['hermes'],self.home)['hermes']
        existing = dest/'sdd-code-review/SKILL.md'; existing.parent.mkdir(parents=True); existing.write_text('local work')
        result = self.cli('install','--source',str(self.source),'--agent','all')
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(existing.read_text(),'local work')
        self.assertFalse((self.home/'.codex').exists())
        self.assertFalse((self.home/'.zcode').exists())

    def test_pending_transaction_blocks_new_writes_across_selected_targets(self):
        dest = target_directories(['pi'],self.home)['pi']
        installation = Installation(dest); installation.state.mkdir(parents=True)
        installation.journal_path.write_text('{}')
        result = self.cli('install','--source',str(self.source),'--agent','all')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('recover',result.stderr)
        self.assertFalse((self.home/'.codex').exists())

    def test_explicit_destination_keeps_legacy_output_and_rejects_ambiguous_multi(self):
        dest=self.base/'legacy-skills'
        result=self.cli('install','--source',str(self.source),'--dest',str(dest))
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['skills'],12)
        self.assertNotIn('agents',json.loads(result.stdout))
        result=self.cli('status','--agent','all','--dest',str(dest))
        self.assertNotEqual(result.returncode,0)

    def test_read_only_status_creates_no_directories(self):
        result=self.cli('status','--agent','all')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(all(not r['installed'] for r in json.loads(result.stdout)['agents'].values()))
        self.assertFalse(self.home.exists())

    def test_partial_io_failure_reports_completed_agent_and_retains_recovery(self):
        original=shutil.copytree
        def fail(source,destination,*args,**kwargs):
            if Path(destination)==self.home/'.hermes/skills/sdd-context-handoff':
                Path(destination).mkdir()
                shutil.copyfile(Path(source)/'SKILL.md',Path(destination)/'SKILL.md')
                raise OSError('fixture disk error')
            return original(source,destination,*args,**kwargs)
        from contextlib import redirect_stdout, redirect_stderr
        import io
        output=io.StringIO()
        with patch('sys.argv',['install.py','install','--source',str(self.source),'--agent','codex','hermes','--home',str(self.home)]), \
                patch('install.shutil.copytree',side_effect=fail),redirect_stdout(output),redirect_stderr(io.StringIO()):
            self.assertEqual(main(),1)
        report=json.loads(output.getvalue())
        self.assertEqual(set(report['completed']),{'codex'})
        self.assertEqual(report['failed_agent'],'hermes')
        codex=Installation(self.home/'.codex/skills')
        hermes=Installation(self.home/'.hermes/skills')
        self.assertTrue(codex.status()['installed'])
        self.assertTrue(hermes.status()['pending_recovery'])
        self.assertTrue(hermes.recover()['recovered'])
        self.assertFalse(hermes.status()['installed'])
        self.assertFalse(hermes.status()['pending_recovery'])
        self.assertEqual(codex.status()['changed'],[])


if __name__=='__main__': unittest.main()
