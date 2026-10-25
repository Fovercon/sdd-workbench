import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {mkdtempSync,rmSync} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

test('Node distribution ships shared skills and guidance without project process records',()=>{
 const cache=mkdtempSync(path.join(os.tmpdir(),'sdd-npm-package-'));
 try{
  const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
  const result=JSON.parse(execFileSync(process.platform==='win32'?'npm.cmd':'npm',['pack','--dry-run','--json','--ignore-scripts'],{cwd:root,encoding:'utf8',env:{...process.env,npm_config_cache:cache}}));
  const names=result[0].files.map(f=>f.path);
  assert(names.includes('skills/sdd-workflow-router/SKILL.md'));
  assert(names.includes('CONTRIBUTING.md'));assert(names.includes('SECURITY.md'));
  assert(!names.some(p=>p.startsWith('docs/optimization/')||p.startsWith('docs/releases/')||p.startsWith('.eval-artifacts/')));
  assert(!names.some(p=>p.endsWith('.pyc')||p.includes('__pycache__')));
 }finally{rmSync(cache,{recursive:true,force:true});}
});
