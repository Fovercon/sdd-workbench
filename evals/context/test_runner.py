from pathlib import Path
import os,json,subprocess,tempfile,unittest
from unittest.mock import patch
from run_pi import run

class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        for name in ['project','runtime']:(self.root/name).mkdir()
        (self.root/'prompt.txt').write_text('Synthetic request',encoding='utf-8')
    def test_failed_native_process_is_retained_and_never_overwritten(self):
        with patch('run_pi.shutil.which',return_value='/synthetic/pi'),patch('run_pi.subprocess.run',return_value=subprocess.CompletedProcess([],2)):
            self.assertEqual(run(self.root)['exit_code'],2)
        with self.assertRaises(ValueError):run(self.root)
        if os.name!='nt':self.assertEqual((self.root/'invocation.json').stat().st_mode&0o777,0o600)
    def test_timeout_is_not_success_and_metadata_records_no_sandbox(self):
        with patch('run_pi.shutil.which',return_value='/synthetic/pi'),patch('run_pi.subprocess.run',side_effect=subprocess.TimeoutExpired('synthetic',1)):
            self.assertEqual(run(self.root,timeout=1)['exit_code'],'TIMEOUT')
        self.assertEqual(json.loads((self.root/'invocation.json').read_text(encoding='utf-8'))['permissions'],'instruction scoped, no OS sandbox')
    def test_missing_native_executable_does_not_create_logs(self):
        with patch('run_pi.shutil.which',return_value=None),self.assertRaises(ValueError):run(self.root)
        self.assertFalse((self.root/'events.jsonl').exists())
