#!/usr/bin/env python3
"""Freeze bounded workflow fixtures; preserve ref, inputs and visible-primary context."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SKILLS={'implement':['sdd-implement-slice'],'recover':['sdd-context-handoff','sdd-change-impact']}
PROMPTS={
'implement':'请使用 ../runtime/sdd-implement-slice/SKILL.md，按当前已批准的合成合同完成 CURRENT-CARD.md 中的 S1，补齐回归并记录实际结果。先读项目规则与当前义务，保护其他文件，不提交、不推送、不安装、不扩大任务。',
'recover':'请使用 ../runtime/sdd-context-handoff/SKILL.md 接收 HANDOFF.md，核对当前项目是否可以继续此前的 S1。已有授权仅覆盖符合当前合同的工作；保留显式人工门禁。核对后写新的 RESUME.md，说明实际差异、必要问题和下一步。不提交、不推送、不安装。'}
SKILLS.update(direct=['sdd-workflow-router','sdd-implement-slice','sdd-change-impact','sdd-requirements-contract'],
              visible=SKILLS['implement'],risk=['sdd-workflow-router','sdd-change-impact','sdd-requirements-contract'])
PROMPTS.update(direct='请使用 ../runtime/sdd-workflow-router/SKILL.md。service.py 的 select 把子串当作标识符相等，修复成 README.md 写明的精确相等匹配，补必要回归并实际验证。现已授权这项本地修复，无需再次确认。不提交、不推送、不安装。',
               visible=PROMPTS['implement'],
               risk='请使用 ../runtime/sdd-workflow-router/SKILL.md。有人建议把 service.py 中的租户隔离判断删掉一行，改为登录后可下载所有租户的报告。这能按普通局部修复处理吗？只读核对当前约定，说明最早需要处理的合同和下一步，不修改任何文件，不执行项目测试。')
for case in ('plan-local','plan-durable'):
    SKILLS[case]=['sdd-plan-slices']
    PROMPTS[case]='请使用 ../runtime/sdd-plan-slices/SKILL.md，依据当前已批准的 SPEC.md、实际仓库和 PROPOSAL.md 准备技术设计及行为切片。评估草案是否采纳，说明关键取舍。产物写 design/plan.md、design/tasks.md；如需独立版本回执可写 design/plan-receipt.json。仅授权规划，不实施、不运行项目测试、不安装、不提交、不推送；尚无人工设计批准，保留真实门禁和待决问题，不联系真实用户。'

def prepare(case,output,ref=None):
    output=Path(output).resolve()
    if output.exists():raise ValueError('Output exists')
    revision=subprocess.check_output(['git','rev-parse',ref+'^{commit}'],cwd=ROOT,text=True).strip() if ref else 'WORKTREE'
    output.mkdir(parents=True)
    for skill in SKILLS[case]:
        dest=output/'runtime'/skill
        if ref:
            prefix='skills/'+skill+'/'
            names=subprocess.check_output(['git','ls-tree','-r','--name-only',revision,prefix],cwd=ROOT,text=True).splitlines()
            for name in names:
                rel=name[len(prefix):]
                if rel!='SKILL.md' and not rel.startswith(('references/','scripts/','agents/')):continue
                target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT))
        else:
            shutil.copytree(ROOT/'skills'/skill,dest,ignore=shutil.ignore_patterns('tests','evals','__pycache__','*.pyc','*.pyo'))
    shutil.copytree(ROOT/'evals/context/inputs'/('implement' if case=='visible' else case),output/'project')
    if case=='recover':
        old=output/'project/archive/SPEC-v1.md';handoff=output/'project/HANDOFF.md'
        with handoff.open('a',encoding='utf-8')as stream:stream.write('\nPrior source path: SPEC.md\nPrior SHA256: '+hashlib.sha256(old.read_bytes()).hexdigest()+'\n')
    subprocess.run(['git','init','-b','codex/context-fixture'],cwd=output/'project',check=True,capture_output=True)
    subprocess.run(['git','add','.'],cwd=output/'project',check=True,capture_output=True)
    subprocess.run(['git','-c','user.name=SDD Eval Fixture','-c','user.email=eval@example.invalid','-c','commit.gpgsign=false','commit','-m','Synthetic evaluation baseline'],cwd=output/'project',check=True,capture_output=True)
    (output/'repository.json').write_text(json.dumps({'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=output/'project',text=True).strip(),'kind':'isolated synthetic Git baseline; no remote'},indent=2),encoding='utf-8')
    prompt=PROMPTS[case]
    if case=='visible':
        prompt+='\n\n以下为控制方从当前合成项目逐字节注入的可见原文，不是历史摘要；适用来源未变。它不模拟宿主压缩或已有多轮对话。\n'
        for name in ('AGENTS.md','SPEC.md','PLAN.md','TASKS.md','CURRENT-CARD.md'):
            data=(output/'project'/name).read_bytes()
            prompt+='\nSOURCE '+name+' SHA256 '+hashlib.sha256(data).hexdigest()+'\n'+data.decode()+'\nEND SOURCE\n'
    (output/'prompt.txt').write_text(prompt,encoding='utf-8')
    receipt={name:{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()for p in root.rglob('*')if p.is_file()and '.git'not in p.parts}
             for name,root in [('project',output/'project'),('runtime',output/'runtime')]}
    (output/'input-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    (output/'variant.json').write_text(json.dumps({'source':revision,'case':case,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest()},indent=2),encoding='utf-8')
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',choices=SKILLS,required=True);p.add_argument('--output',required=True);p.add_argument('--ref');a=p.parse_args();print(prepare(a.case,a.output,a.ref))
