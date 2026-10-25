#!/usr/bin/env python3
"""Run one fresh native Pi trial; no live skill/config installation or publication."""
import argparse,datetime,json,os,shutil,subprocess,time
from pathlib import Path


def private_file(path):
    return os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb')


def run(directory,executable='pi',timeout=900):
    base=Path(directory).resolve()
    if not(base/'project').is_dir()or not(base/'runtime').is_dir()or not(base/'prompt.txt').is_file():raise ValueError('Prepare the trial first')
    for name in ['events.jsonl','stderr.log','invocation.json','process-result.json']:
        if(base/name).exists():raise ValueError('Trial logs exist; prepare a new directory')
    exe=shutil.which(executable)
    if not exe:raise ValueError('Native Pi executable unavailable')
    argv=[exe,'--offline','--no-session','--mode','json','--no-extensions','--no-skills','--skill',str(base/'runtime'),'--no-prompt-templates','--no-themes','--no-context-files','--tools','read,bash,edit,write','--provider','deepseek','--model','deepseek-flash','--print',(base/'prompt.txt').read_text(encoding='utf-8')]
    with private_file(base/'invocation.json')as f:f.write(json.dumps({'argv':argv,'cwd':str(base/'project'),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'permissions':'instruction scoped, no OS sandbox','backend_revision':'NOT_REPORTED'},ensure_ascii=False,indent=2).encode())
    start=time.monotonic()
    with private_file(base/'events.jsonl')as out,private_file(base/'stderr.log')as err:
        try:code=subprocess.run(argv,cwd=base/'project',stdout=out,stderr=err,timeout=timeout).returncode
        except subprocess.TimeoutExpired:code='TIMEOUT'
    result={'exit_code':code,'seconds':time.monotonic()-start}
    with private_file(base/'process-result.json')as f:f.write(json.dumps(result).encode())
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory');p.add_argument('--executable',default='pi');p.add_argument('--timeout',type=int,default=900);a=p.parse_args()
    if a.timeout<=0:p.error('timeout must be positive')
    r=run(a.directory,a.executable,a.timeout);print(json.dumps(r));raise SystemExit(0 if r['exit_code']==0 else 1)
