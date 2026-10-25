"""Typed presentation records for rules, clarification, execution and delivery."""

SECTIONS = {
    'Constitution': {'constraint': '项目约束', 'command': '开发与检查命令'},
    'Align': {'context': '问题背景', 'assumption': '尚需核实的假设'},
    'Implement': {'implementation': '实现说明', 'test_run': '测试与运行记录'},
    'Finish': {'deliverable': '交付物', 'usage': '使用方法', 'limitation': '已知限制与待办',
               'handoff': '接续工作', 'recovery': '恢复与回退方法'},
}
RESULTS = {'PASS': '通过', 'FAIL': '失败', 'NOT_RUN': '未执行', 'UNKNOWN': '结果未知'}
DELIVERY = {'PLANNED': '计划交付', 'PREPARED': '已准备，待交付', 'DELIVERED': '有交付记录'}


def validate(snapshot):
    from .workstream import references
    nodes = {i['id']: i for i in snapshot['items']}
    for item in snapshot['items']:
        if 'stage_detail' not in item:
            continue
        detail = item['stage_detail']
        if (not isinstance(detail, dict) or not isinstance(detail.get('type'), str)
                or detail['type'] not in SECTIONS.get(item.get('stage'), {})):
            raise ValueError('stage_detail.type must belong to its owning stage')
        if ('lifecycle' not in snapshot or item['view'] not in ('progress', 'capability')
                or 'work' in item or not item.get('sources') or not item.get('note', '').strip()):
            raise ValueError('stage_detail needs a stage, sources, explanation and progress/capability view; work stays separate')
        role = detail['type']
        fields = {'type', 'record_ids'}
        if role in ('command', 'test_run', 'usage', 'recovery'): fields |= {'command', 'cwd'}
        if role in ('command', 'test_run'): fields.add('result')
        if role in ('usage', 'recovery', 'handoff'): fields.add('steps')
        if role == 'handoff': fields.add('owner')
        if role == 'deliverable': fields |= {'path', 'delivery_status', 'delivery_receipt'}
        if set(detail) - fields:
            raise ValueError('Unknown stage_detail field for ' + role)
        for key in ('command', 'cwd', 'path', 'owner', 'delivery_receipt'):
            if key in detail and (not isinstance(detail[key], str) or not detail[key].strip()):
                raise ValueError('stage_detail.' + key + ' must be nonempty text')
        for key in ('record_ids', 'steps'):
            if key in detail and (not isinstance(detail[key], list)
                    or any(not isinstance(v, str) or not v.strip() for v in detail[key])
                    or len(set(detail[key])) != len(detail[key])):
                raise ValueError('stage_detail.' + key + ' must be a unique string list')
            if key == 'steps' and key in detail and not detail[key]:
                raise ValueError('stage_detail.steps must not be empty')
        for key in detail.get('record_ids', []):
            if key not in nodes or key == item['id']:
                raise ValueError('stage_detail record_ids must identify other existing records')
        if role == 'command' and 'command' not in detail:
            raise ValueError('command record needs its exact command text')
        if role == 'test_run' and 'result' not in detail:
            raise ValueError('test_run needs an explicit result')
        if 'result' in detail:
            if detail['result'] not in RESULTS:
                raise ValueError('stage_detail result must use PASS, FAIL, NOT_RUN or UNKNOWN')
            if detail['result'] in ('PASS', 'FAIL') and item['kind'] != 'runtime_evidence':
                raise ValueError('Executed results need runtime_evidence')
        if role == 'deliverable':
            if detail.get('delivery_status') not in DELIVERY:
                raise ValueError('deliverable needs an explicit delivery_status')
            if detail['delivery_status'] != 'PLANNED' and not detail.get('path'):
                raise ValueError('Prepared/delivered output needs its actual path')
            if detail.get('path') and detail['delivery_status'] != 'PLANNED' and detail['path'] not in [r['path'] for r in item['sources']]:
                raise ValueError('Prepared/delivered output must cite its own file')
            if detail['delivery_status'] == 'DELIVERED' and item['kind'] != 'runtime_evidence':
                raise ValueError('DELIVERED needs a real delivery record, not file existence')
            if 'delivery_receipt' in detail and detail['delivery_status'] != 'DELIVERED':
                raise ValueError('delivery_receipt belongs to an explicitly recorded delivery')
            if detail['delivery_status'] == 'DELIVERED' and (not detail.get('delivery_receipt')
                    or detail['delivery_receipt'] == detail.get('path')
                    or detail['delivery_receipt'] not in [r['path'] for r in item['sources']]):
                raise ValueError('DELIVERED needs a separate cited delivery_receipt')
    visiting, visited = set(), set()
    def walk(key):
        if key in visiting: raise ValueError('Evidence record references must be acyclic')
        if key in visited: return
        visiting.add(key)
        for target in references(nodes[key]): walk(target)
        visiting.remove(key); visited.add(key)
    for key in nodes: walk(key)


def inspect(root, items):
    from .evidence import source_path
    for item in items:
        detail = item.get('stage_detail', {})
        if detail.get('delivery_receipt') and detail.get('path'):
            output = source_path(root, detail['path'])
            receipt = source_path(root, detail['delivery_receipt'])
            if output == receipt or (output.is_file() and receipt.is_file() and output.samefile(receipt)):
                raise ValueError('Delivery output and receipt must be distinct files, not path aliases or hardlinks')
        for key in ('path', 'cwd', 'delivery_receipt'):
            if key in detail:
                source_path(root, detail[key])  # Includes symlink/traversal trust-boundary checks.
        for key in ('path', 'delivery_receipt'):
            if detail.get(key) and source_path(root, detail[key]).is_dir():
                raise ValueError('deliverable and receipt must identify files, not directories')
