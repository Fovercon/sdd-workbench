#!/usr/bin/env python3
"""Freeze implementation/recovery guard fixtures; not a token-efficiency comparison."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SKILLS={'implement':['sdd-implement-slice'],'recover':['sdd-context-handoff','sdd-change-impact']}
PROMPTS={
'implement':'请使用 ../runtime/sdd-implement-slice/SKILL.md，按当前已批准的合成合同完成 CURRENT-CARD.md 中的 S1，补齐回归并记录实际结果。先读项目规则与当前义务，保护其他文件，不提交、不推送、不安装、不扩大任务。',
'recover':'请使用 ../runtime/sdd-context-handoff/SKILL.md 接收 HANDOFF.md，核对当前项目是否可以继续此前的 S1。已有授权仅覆盖符合当前合同的工作；保留显式人工门禁。核对后写新的 RESUME.md，说明实际差异、必要问题和下一步。不提交、不推送、不安装。'}

def prepare(case,output):
    output=Path(output).resolve()
    if output.exists():raise ValueError('Output exists')
    output.mkdir(parents=True)
    for skill in SKILLS[case]:
        shutil.copytree(ROOT/'skills'/skill,output/'runtime'/skill,ignore=shutil.ignore_patterns('tests','evals','__pycache__','*.pyc'))
    shutil.copytree(ROOT/'evals/context/inputs'/case,output/'project')
    if case=='recover':
        old=output/'project/archive/SPEC-v1.md';handoff=output/'project/HANDOFF.md'
        with handoff.open('a',encoding='utf-8')as stream:stream.write('\nPrior source path: SPEC.md\nPrior SHA256: '+hashlib.sha256(old.read_bytes()).hexdigest()+'\n')
    subprocess.run(['git','init','-b','codex/context-fixture'],cwd=output/'project',check=True,capture_output=True)
    subprocess.run(['git','add','.'],cwd=output/'project',check=True,capture_output=True)
    subprocess.run(['git','-c','user.name=SDD Eval Fixture','-c','user.email=eval@example.invalid','-c','commit.gpgsign=false','commit','-m','Synthetic evaluation baseline'],cwd=output/'project',check=True,capture_output=True)
    (output/'repository.json').write_text(json.dumps({'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=output/'project',text=True).strip(),'kind':'isolated synthetic Git baseline; no remote'},indent=2),encoding='utf-8')
    (output/'prompt.txt').write_text(PROMPTS[case],encoding='utf-8')
    receipt={name:{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()for p in root.rglob('*')if p.is_file()and '.git'not in p.parts}
             for name,root in [('project',output/'project'),('runtime',output/'runtime')]}
    (output/'input-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(output)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',choices=SKILLS,required=True);p.add_argument('--output',required=True);a=p.parse_args();prepare(a.case,a.output)
