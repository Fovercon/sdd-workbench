"""Four-stage synthetic sources; no production progress, approval or delivery."""
import hashlib,json
from pathlib import Path
from workstream_fixture import fixture as mainline


def fixture(root):
    root = Path(root); data = mainline(root)
    def ref(path):
        return dict(path=path,line=1,sha256=hashlib.sha256((root/path).read_bytes()).hexdigest())
    def add(key,label,stage,detail=None,paths=None,**extra):
        path='stage-'+key.replace('/','_')+'.md'
        (root/path).write_text('# 合成评测记录，不代表真实运行或批准\n'+label+'\n'+json.dumps(detail or {},ensure_ascii=False),encoding='utf-8')
        item=dict(id=key,label=label,stage=stage,view='capability' if detail else 'progress',kind='assessment',state='SATISFIED',note=extra.pop('note',label+'。仅用于界面回归。'),sources=[ref(p) for p in (paths or [path])])
        if detail:item['stage_detail']=detail
        item.update(extra);data['items'].append(item);return item
    for stage in ['Constitution','Finish']:
        add(stage,stage+' 阶段记录',stage)
        data['lifecycle']['stage_items'][stage]=stage
    data['lifecycle']['current_stage']='Finish'
    add('rule','保留未管理的文件','Constitution',dict(type='constraint'),note='仅修改本轮范围内的文件，保留用户输入和历史记录。')
    add('command 中文%','本地检查命令','Constitution',dict(type='command',command='python3 -m unittest discover -s tests\n# 合成命令，仅供阅读',cwd='.',result='NOT_RUN'),note='这是文档中的检查命令，本次尚未执行。')
    add('context','资料人员难以确认任务恢复范围','Align',dict(type='context'),note='需要明确暂停后继续处理哪些资料，以及哪些结果必须保留。')
    add('assumption','恢复时成功结果不应被重复处理','Align',dict(type='assumption'),note='此项仍需核实，不作为已经批准的业务规则。',state='UNKNOWN')
    add('question','确认恢复范围','Align',state='PENDING_HUMAN',note='尚未收到范围答复。',decision=dict(id='Q-scope',kind='input',prompt='暂停后恢复时，需要保留哪些已完成结果？',owner='演示项目负责人',scope='仅合成评测的恢复范围'))
    add('implementation','暂停接口已实现，继续处理尚未完成','Implement',dict(type='implementation',record_ids=['code2','S2']),note='当前仅有暂停标记，继续执行路径仍需开发。')
    add('run-pass','编号匹配检查','Implement',dict(type='test_run',command='python3 -m unittest test_scope',cwd='.',result='PASS',record_ids=['code1']),kind='runtime_evidence',note='预置运行结果为通过，仅覆盖编号匹配。')
    add('run-fail','成功结果保护检查','Implement',dict(type='test_run',command='python3 -m unittest test_preservation',result='FAIL',record_ids=['code2']),kind='runtime_evidence',note='预置运行结果为失败：原成功项的时间被修改。')
    add('run-pending','暂停后继续的浏览器检查','Implement',dict(type='test_run',result='NOT_RUN',record_ids=['S2']),note='尚未执行，不存在通过结论。')
    (root/'candidate.md').write_text('合成本地候选文件\n',encoding='utf-8')
    (root/'delivered.md').write_text('合成已交付文件\n',encoding='utf-8')
    (root/'delivery-receipt.json').write_text('{"synthetic":true,"delivery":"recorded"}\n')
    add('candidate','本地候选说明','Finish',dict(type='deliverable',path='candidate.md',delivery_status='PREPARED',record_ids=['run-pass']),paths=['candidate.md'],note='文件已准备，但没有实际交付记录。')
    add('delivered','合成交付说明','Finish',dict(type='deliverable',path='delivered.md',delivery_status='DELIVERED',delivery_receipt='delivery-receipt.json'),paths=['delivered.md','delivery-receipt.json'],kind='runtime_evidence',note='仅演示有回执的交付记录，不代表真实项目交付或发布批准。')
    add('planned','计划中的操作指南','Finish',dict(type='deliverable',path='future-guide.md',delivery_status='PLANNED'),note='仅计划交付，该文件尚不存在。')
    add('usage','本地使用步骤','Finish',dict(type='usage',steps=['进入项目目录。','按来源说明启动候选，核对界面提示。'],command='python3 app.py',cwd='.'),note='本地使用说明，不提供自动启动。')
    add('limit','尚未验证真实治理模型','Finish',dict(type='limitation'),note='当前仅为演示执行器，不能作为真实治理结果。',state='GAP')
    add('handoff','继续完成暂停恢复验证','Finish',dict(type='handoff',owner='演示维护者',steps=['补齐继续处理功能。','完成浏览器验证并保留记录。']),note='接续工作仍未完成。')
    add('recovery','保留数据后恢复上一个候选','Finish',dict(type='recovery',steps=['先停止本地任务。','保留当前数据，再按项目说明恢复备份。']),note='本页不执行恢复或删除操作。')
    data.update(project_id='four-stage-synthetic',title='四阶段阅读演示（合成数据）',summary='展示项目规则、需求澄清、开发与测试、交付收尾；所有业务状态均为合成评测输入。')
    return data


if __name__=='__main__':
    import sys
    root=Path(sys.argv[1]);data=fixture(root)
    (root/'input.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
