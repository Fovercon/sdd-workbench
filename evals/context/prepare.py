#!/usr/bin/env python3
"""Freeze a VIEW context trial without installing skills or exposing its evaluator."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]


def prepare(output,ref=None):
    output=Path(output).resolve()
    if output.exists():raise ValueError('Output exists; preserve the earlier trial')
    runtime=output/'runtime/sdd-workflow-router';runtime.mkdir(parents=True)
    prefix='skills/sdd-workflow-router/'
    if ref:
        revision=subprocess.check_output(['git','rev-parse',ref+'^{commit}'],cwd=ROOT,text=True).strip()
        names=subprocess.check_output(['git','ls-tree','-r','--name-only',revision,prefix],cwd=ROOT,text=True).splitlines()
        entries=[(p[len(prefix):],subprocess.check_output(['git','show',revision+':'+p],cwd=ROOT))for p in names
                 if p[len(prefix):]=='SKILL.md'or p[len(prefix):].startswith(('references/','scripts/','agents/'))]
    else:
        revision='WORKTREE'
        entries=[(p.relative_to(ROOT/prefix).as_posix(),p.read_bytes())for p in(ROOT/prefix).rglob('*')if p.is_file()
                 and '__pycache__'not in p.parts and (p.name=='SKILL.md'or p.relative_to(ROOT/prefix).parts[0]in('references','scripts','agents'))]
    for name,data in entries:
        p=runtime/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    project=output/'project';shutil.copytree(ROOT/prefix/'evals/forward/inputs/stage-reading',project)
    prompt=('请使用随附 SDD skill，为第一次接触项目的研发工程师生成离线看板，重点展示项目规则、需求澄清、开发与测试、交付收尾四个阶段。'
            '先读当前目录原始材料和 ../runtime/sdd-workflow-router/SKILL.md，并加载相关VIEW参考。呈现约束与命令、问题目标与待确认事项、实现和运行结果、交付准备/使用方法/限制/接续。'
            '明确是合成输入，保留未知和未执行项，不编造审批、交付回执或发布结论。原始文件只读，只可新建观察文件和独立的看板版本目录（例如 view-v1、view-v2），'
            '任何已经生成的完整看板都必须保留；修订后使用新版本目录，不删除、覆盖或直接修改旧版，可用 python3 调用随附渲染器；不得执行项目示例命令或测试。'
            '真实浏览器由控制方另行核对，不得预报通过。不提交、不推送、不安装。')
    (output/'prompt.txt').write_text(prompt,encoding='utf-8')
    receipt={name:{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()for p in root.rglob('*')if p.is_file()}
             for name,root in [('project',project),('runtime',runtime)]}
    (output/'input-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    (output/'variant.json').write_text(json.dumps({'source':revision,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest()},indent=2),encoding='utf-8')
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);p.add_argument('--ref')
    a=p.parse_args();print(prepare(a.output,a.ref))
