"""Optional source-bound work records. Execution, evidence and acceptance differ."""
from . import lifecycle

ROLES = {'brief', 'requirement', 'slice', 'check'}
EXECUTION = {'TODO': '待开始', 'DOING': '进行中', 'BLOCKED': '受阻', 'DONE': '已完成'}
RESULTS = {'PASS': '通过', 'FAIL': '失败', 'NOT_RUN': '未执行', 'UNKNOWN': '结果未知'}
FIELDS = {'brief': {'in_scope', 'out_of_scope'}, 'requirement': {'acceptance'},
          'slice': {'requirement_ids', 'depends_on', 'status', 'blocker'},
          'check': {'requirement_ids', 'slice_ids', 'result', 'acceptance_refs'}}
REQUIRED_LISTS = {'brief': ('in_scope', 'out_of_scope'), 'requirement': ('acceptance',),
                  'slice': ('requirement_ids',), 'check': ('requirement_ids', 'slice_ids')}
OWNING_STAGE = {'requirement': 'Spec', 'slice': 'Tasks', 'check': 'Converge'}


def references(item):
    work = item.get('work', {})
    return (work.get('requirement_ids', []) + work.get('depends_on', [])
            + work.get('slice_ids', []) + item.get('implementation_ids', [])
            + item.get('stage_detail', {}).get('record_ids', []))


def validate(snapshot):
    nodes = {i['id']: i for i in snapshot['items']}
    typed = [i for i in snapshot['items'] if 'work' in i]
    if typed and 'lifecycle' not in snapshot:
        raise ValueError('work records need lifecycle stage bindings')
    if sum(i.get('work', {}).get('type') == 'brief' for i in typed if isinstance(i.get('work'), dict)) > 1:
        raise ValueError('Only one source-bound project brief is allowed')
    for item in typed:
        work = item['work']
        if not isinstance(work, dict) or work.get('type') not in ROLES:
            raise ValueError('work.type must be brief, requirement, slice or check')
        role = work['type']
        fields = FIELDS[role]
        if set(work) - fields - {'type'}:
            raise ValueError('Unknown work field for ' + role)
        if not item.get('sources'):
            raise ValueError('work records must cite their own sources')
        expected = OWNING_STAGE
        if role in expected and (item.get('stage') != expected[role] or item['view'] != 'capability'):
            raise ValueError('work role needs its owning stage and capability view')
        if role == 'brief' and (not item.get('stage') or item['view'] != 'progress'):
            raise ValueError('brief needs a stage-bound progress record')
        required = REQUIRED_LISTS[role]
        for key in (*required, *(['depends_on'] if 'depends_on' in work else [])):
            value = work.get(key)
            if (not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value)
                    or len(set(value)) != len(value)):
                raise ValueError('work.' + key + ' must be a unique list of nonempty strings')
            if key in ('acceptance', 'requirement_ids', 'slice_ids') and not value:
                raise ValueError('work.' + key + ' must not be empty')
        if role == 'slice':
            if work.get('status') not in EXECUTION:
                raise ValueError('slice needs TODO, DOING, BLOCKED or DONE status')
            if 'blocker' in work and (not isinstance(work['blocker'], str) or not work['blocker'].strip()):
                raise ValueError('blocker must be nonempty text')
            if work['status'] == 'BLOCKED' and not work.get('blocker'):
                raise ValueError('BLOCKED slice needs a concrete blocker')
        if role == 'check':
            if work.get('result') not in RESULTS:
                raise ValueError('check needs PASS, FAIL, NOT_RUN or UNKNOWN result')
            if work['result'] == 'PASS' and item['kind'] != 'runtime_evidence':
                raise ValueError('PASS needs runtime_evidence, not a planned test or assessment')
    for item in typed:
        work = item['work']
        for key, role in [('requirement_ids', 'requirement'), ('depends_on', 'slice'), ('slice_ids', 'slice')]:
            for ref in work.get(key, []):
                target = nodes.get(ref)
                if target is None or target.get('work', {}).get('type') != role or ref == item['id']:
                    raise ValueError('work links must identify existing records of the required type')
        if work['type'] == 'check':
            slices = [nodes[s]['work']['requirement_ids'] for s in work['slice_ids']]
            if (not set(work['requirement_ids']) <= set().union(*map(set, slices))
                    or any(not set(reqs) & set(work['requirement_ids']) for reqs in slices)):
                raise ValueError('check requirement and slice links must describe the same scope')
            mapping = work.get('acceptance_refs', {})
            if not isinstance(mapping, dict) or set(mapping) - set(work['requirement_ids']):
                raise ValueError('acceptance_refs must map the check requirement IDs to acceptance indexes')
            for key, indexes in mapping.items():
                if (not isinstance(indexes, list) or not indexes
                        or any(type(n) is not int or n < 1 or n > len(nodes[key]['work']['acceptance']) for n in indexes)
                        or len(set(indexes)) != len(indexes)):
                    raise ValueError('acceptance_refs indexes must be unique 1-based acceptance positions')
    visiting, visited = set(), set()

    def walk(key):
        if key in visiting:
            raise ValueError('work dependencies must be acyclic')
        if key in visited:
            return
        visiting.add(key)
        for ref in references(nodes[key]):
            if 'work' in nodes[ref]:
                walk(ref)
        visiting.remove(key)
        visited.add(key)
    for item in typed:
        walk(item['id'])


def propagate(items):
    """Invalidate downstream source identity; never refresh expected fingerprints."""
    nodes = {i['id']: i for i in items}
    visited = set()

    def walk(item):
        if item['id'] in visited:
            return
        linked = [nodes[k] for k in references(item)] if 'work' in item or 'stage_detail' in item else []
        for target in linked:
            walk(target)
        states = [i['freshness'] for i in [item, *linked]]
        item['freshness'] = 'UNKNOWN' if 'UNKNOWN' in states else 'STALE' if 'STALE' in states else 'CURRENT'
        item['effective_state'] = item['state'] if item['freshness'] == 'CURRENT' else item['freshness']
        visited.add(item['id'])
    for item in items:
        if 'work' in item or 'stage_detail' in item:
            walk(item)


def model(snapshot, items):
    nodes = {i['id']: i for i in items}
    stages = {s['name']: s['status'] for s in lifecycle.stage_status(snapshot, items)}
    grouped = {role: [i for i in items if i.get('work', {}).get('type') == role] for role in ROLES}

    usable_cache = {}

    def usable(item):
        key = item['id']
        if key not in usable_cache:
            usable_cache[key] = (item['effective_state'] == 'SATISFIED'
                and stages.get(item.get('stage')) not in ('REVISIT', 'STALE', 'UNKNOWN')
                and all(usable(nodes[k]) for k in references(item)))
        return usable_cache[key]

    issue_cache = {}

    def slice_issues(item):
        if item['id'] in issue_cache:
            return issue_cache[item['id']]
        problems = []
        if not usable(item):
            problems.append('任务记录需核对')
        if any(not usable(nodes[k]) for k in item['work']['requirement_ids']):
            problems.append('对应需求的记录需核对')
        if item['work']['status'] != 'DONE':
            problems.append('任务' + EXECUTION[item['work']['status']])
        if item['work'].get('blocker'):
            problems.append('阻塞：' + item['work']['blocker'])
        if not item.get('implementation_ids'):
            problems.append('未关联实现文件')
        elif not all(usable(nodes[k]) for k in item['implementation_ids']):
            problems.append('实现文件的记录需核对')
        for key in item['work'].get('depends_on', []):
            # Validation guarantees a DAG; propagate readiness, not just status.
            if slice_issues(nodes[key]):
                problems.append('前置任务尚未完成或需核对：' + nodes[key]['label'])
        issue_cache[item['id']] = problems
        return problems

    rows = []
    for req in grouped['requirement']:
        slices = [s for s in grouped['slice'] if req['id'] in s['work']['requirement_ids']]
        checks = [c for c in grouped['check'] if req['id'] in c['work']['requirement_ids']]
        gaps = []
        if not usable(req):
            gaps.append('需求记录需核对')
        if not slices:
            gaps.append('尚未安排任务')
        for s in slices:
            gaps.extend(s['label'] + '：' + issue for issue in slice_issues(s))
            applicable = [c for c in checks if s['id'] in c['work']['slice_ids']]
            if not applicable:
                gaps.append(s['label'] + '：缺少验证记录')
        for c in checks:
            if not usable(c):
                gaps.append(c['label'] + '：验证记录需核对')
            elif c['work']['result'] != 'PASS':
                gaps.append(c['label'] + '：' + RESULTS[c['work']['result']])
            if not c['work'].get('acceptance_refs', {}).get(req['id']):
                gaps.append(c['label'] + '：未关联具体验收条件')
        acceptance_coverage = []
        for index, text in enumerate(req['work']['acceptance'], 1):
            applicable = [c for c in checks if index in c['work'].get('acceptance_refs', {}).get(req['id'], [])]
            passed = any(usable(c) and c['work']['result'] == 'PASS' for c in applicable)
            acceptance_coverage.append({'index': index, 'text': text, 'checks': applicable, 'passed': passed})
            if not passed:
                gaps.append(f'验收条件 {index} 缺少有效的通过记录：{text}')
        verdict = 'RECHECK' if any(i['freshness'] != 'CURRENT' or stages.get(i.get('stage')) in ('REVISIT', 'STALE', 'UNKNOWN')
                                 for i in [req, *slices, *checks]) else 'GAP' if gaps else 'COVERED'
        rows.append({'item': req, 'slices': slices, 'checks': checks,
                     'gaps': list(dict.fromkeys(gaps)), 'verdict': verdict, 'acceptance': acceptance_coverage})
    return dict(grouped, rows=rows, nodes=nodes, usable=usable,
                slice_issues=slice_issues, covered=sum(r['verdict'] == 'COVERED' for r in rows))
