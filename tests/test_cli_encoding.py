"""Reproduce non-UTF-8 Windows pipes without hiding locale defaults in CI."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]


class CliEncoding(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name).resolve();self.home=self.base/'中文-profile'
        self.env=dict(os.environ);self.env['PYTHONIOENCODING']='cp1252';self.env['PYTHONUTF8']='0'

    def run_cli(self,tool,*args,encoding='ascii'):
        return subprocess.run([sys.executable,'-B',str(ROOT/'tools'/tool),*args],env=self.env,
                              capture_output=True,text=True,encoding=encoding)

    def test_json_protocols_preserve_unicode_over_legacy_encoded_pipes(self):
        result=self.run_cli('install.py','install','--dry-run','--home',str(self.home))
        self.assertEqual(result.returncode,0,result.stderr)
        preview=json.loads(result.stdout)
        self.assertIn('中文-profile',preview['agents']['codex']['destination'])
        result=self.run_cli('doctor.py','--json','--home',str(self.home))
        self.assertEqual(result.returncode,1,result.stderr)
        report=json.loads(result.stdout)
        self.assertEqual(report['summary'],'NEEDS_ATTENTION')
        self.assertIn('未在',report['issues'][0]['message'])
        root=self.base/'reports';(root/'evidence').mkdir(parents=True)
        data='实际观察\n'.encode('utf-8');(root/'evidence/中文.txt').write_bytes(data)
        result=self.run_cli('review.py','evidence','--root',str(root),'--path','evidence/中文.txt')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout),{'path':'evidence/中文.txt','sha256':hashlib.sha256(data).hexdigest()})
        self.assertFalse(self.home.exists())

    def test_human_doctor_emits_utf8_under_legacy_pipe_default(self):
        result=self.run_cli('doctor.py','--home',str(self.home),encoding='utf-8')
        self.assertEqual(result.returncode,1,result.stderr)
        self.assertIn('只读诊断',result.stdout)
        self.assertFalse(self.home.exists())
