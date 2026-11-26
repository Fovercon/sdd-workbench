"""Run artifacts: report.json/report.md, run index and acceptance marking."""
import json
from pathlib import Path

from runner import compare
from runner.paths import runs_root


def _fmt(value):
    if value is None:
        return '—'
    if isinstance(value, bool):
        return '是' if value else '否'
    if isinstance(value, float):
        return f'{value:.4f}'.rstrip('0').rstrip('.')
    return str(value)


def index_path():
    return runs_root() / 'index.json'


def load_index():
    path = index_path()
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    return {'runs': [], 'accepted_run_id': None}


def save_index(index):
    path = index_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')


def upsert_run(entry):
    index = load_index()
    index['runs'] = [r for r in index['runs'] if r['run_id'] != entry['run_id']] + [entry]
    index['runs'].sort(key=lambda r: r.get('created_utc', ''))
    save_index(index)


def accept(run_id):
    run_dir = runs_root() / run_id
    if not (run_dir / 'report.json').is_file():
        raise ValueError(f'{run_id} has no report.json; complete the run first')
    index = load_index()
    index['accepted_run_id'] = run_id
    for run in index['runs']:
        if run['run_id'] == run_id:
            run['accepted'] = True
    save_index(index)
    return index


def load_accepted_report(exclude_run_id=None):
    index = load_index()
    accepted = index.get('accepted_run_id')
    if not accepted or accepted == exclude_run_id:
        return None
    path = runs_root() / accepted / 'report.json'
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    return None


def optimization_hints(report):
    """Data-backed next-step suggestions; every line cites its source table."""
    hints = []
    l1 = (report.get('l1') or {}).get('aggregate') or {}
    per_skill = l1.get('per_skill') or {}
    weak = sorted((s for s in per_skill.values() if s.get('recall') is not None),
                  key=lambda s: s['recall'])[:3]
    if weak:
        names = ', '.join(f"{n}(recall {_fmt(per_skill[n]['recall'])})"
                          for n in [k for k, v in per_skill.items() if v in weak])
        hints.append(f"L1 必需读取薄弱:{names} —— 先核对原始工具结果、判定器覆盖与任务是否确需该技能,再重复验证候选入口。")
    confusion = l1.get('confusion_pairs') or {}
    for pair, count in sorted(confusion.items(), key=lambda kv: -kv[1])[:3]:
        hints.append(f"L1 相邻混淆:{pair} 共 {count} 例 —— 复核原始阶段顺序、允许邻居和实际行为,不由读取集合直接推断路由错误。")
    negatives = l1.get('negatives') or {}
    if negatives.get('false_positives'):
        cases = ', '.join(c['case'] for c in negatives['cases'][:5])
        hints.append(f"L1 负例误触发 {negatives['false_positives']}/{negatives['n']}(如 {cases})—— 收紧触发范围。")
    l2 = (report.get('l2') or {}).get('aggregate') or {}
    fvb = l2.get('full_vs_baseline') or {}
    gains = fvb.get('normalized_gain_per_task') or {}
    negative_tasks = [t for t, g in gains.items() if g is not None and g < 0]
    if negative_tasks:
        hints.append(f"L2 套件负贡献任务:{', '.join(sorted(negative_tasks))} —— 复查该场景是否被过度流程拖累。")
    conditions = l2.get('conditions') or {}
    full_mean = (conditions.get('full') or {}).get('mean_partial')
    for cond, metrics in sorted(conditions.items()):
        if cond in ('full', 'baseline') or full_mean is None:
            continue
        delta = round(metrics['mean_partial'] - full_mean, 4)
        label = 'router+条件类 skill' if cond == 'core5' else cond
        if delta > 0.02:
            hints.append(f"L2 消融 {cond}({label})比 full 高 {delta} —— 检查该子集引入的开销或误导。")
        elif delta < -0.02:
            hints.append(f"L2 消融 {cond}({label})比 full 低 {abs(delta)} —— 该子集贡献显著,保持。")
    inv = (conditions.get('full') or {}).get('invocation_rate')
    if inv is not None and inv < 0.9:
        hints.append(f"L2 full 条件 skill 调用率仅 {_fmt(inv)} —— 先解决触发,再谈效果。")
    directed = conditions.get('directed')
    if directed is not None:
        d_inv = directed.get('invocation_rate')
        if d_inv is not None and d_inv < 0.9:
            hints.append(f"L2 directed(被明确引导)调用率仅 {_fmt(d_inv)} —— 引导后仍不加载,查 description/发现机制。")
        d_full = directed.get('mean_partial')
        if d_full is not None and full_mean is not None and d_full - full_mean > 0.02:
            hints.append(f"directed 比 organic full 高 {round(d_full - full_mean, 4)} —— 套件被真正使用时有增益,优先打通触发。")
        if d_full is not None and full_mean is not None and d_full - full_mean < -0.02:
            hints.append(f"directed 比 organic full 低 {abs(round(d_full - full_mean, 4))} —— 加载 skills 反而拖累,检查技能内容与开销。")
    overhead = (l2.get('full_vs_baseline') or {}).get('input_ratio')
    if overhead is not None and overhead > 1.3:
        hints.append(f"skill 目录常驻使每请求 input 增至 {overhead}× —— 精简 description 总预算(SUITE-POLICY §2)。")
    l3 = (report.get('l3') or {}).get('aggregate') or {}
    if l3.get('fabricated_claims'):
        hints.append(f"L3 编造'全部通过'声明 {l3['fabricated_claims']} 例 —— 强化 converge/implement 的证据语言。")
    if l3.get('reward_hack_slots'):
        hints.append(f"L3 visible-held-out 差距>0.5 共 {len(l3['reward_hack_slots'])} 例 —— 测试设计过松。")
    if not hints:
        hints.append('各层均未见明显短板;可加大任务集/ trial 数提高置信度。')
    return hints


def render_markdown(report):
    lines = []
    manifest = report.get('manifest') or {}
    lines.append(f"# SDD Workbench 回归评测报告 — {report['run_id']}")
    lines.append('')
    lines.append(f"- 档位:{report.get('profile')}  |  套件版本引用:{manifest.get('suite_ref')}"
                 f"(rev {str(manifest.get('revision'))[:12]},{'有未提交改动' if manifest.get('dirty') else '干净'})")
    pi_env = manifest.get('pi_environment') or {}
    lines.append(f"- 运行时快照哈希:{str(manifest.get('snapshot_hash'))[:16]}…  |  "
                 f"Pi:{str(pi_env.get('pi_version') or pi_env.get('executable'))[:60]}")
    lines.append(f"- 模型:{manifest.get('provider_model')}(backend_revision: NOT_REPORTED;以原始 events 为准)")
    lines.append('- 单次运行是试点而非可靠性估计;所有比率均附原始计数。')
    lines.append('')
    gates = report.get('gates') or []
    if gates:
        lines.append('## 验收门')
        lines.append('')
        lines.append('| 门 | 观测 | 阈值 | 结果 |')
        lines.append('|---|---|---|---|')
        for gate in gates:
            mark = '缺失' if gate['missing'] else ('✅' if gate['passed'] else '❌')
            lines.append(f"| {gate['id']} | {_fmt(gate['observed'])} | "
                         f"{gate['op']} {gate['threshold']} | {mark} |")
        lines.append('')
    l1 = (report.get('l1') or {}).get('aggregate')
    if l1:
        lines.append('## L1 触发/路由')
        lines.append('')
        lines.append(f"用例 {l1['n_cases']},读取集合符合预期 {l1['n_correct']};负例精确率 "
                     f"{_fmt(l1.get('negative_precision'))};结果枚举纪律 {_fmt(l1.get('enum_discipline'))}。")
        lines.append('成功读取是技能正文/参考的暴露证据,不证明已执行该技能或行为正确;允许的邻居不计误触发。')
        if l1.get('n_invalid'):
            lines.append(f"无效运行 {l1['n_invalid']} 个(退出异常、最终答复缺失或事件解析错误),不纳入读取/负例比率。")
        if 'n_strict_correct' in l1:
            lines.append(f"严格集合一致:{l1['n_strict_correct']}/{l1['n_cases']}(单独诊断,不处罚允许邻居)。")
        lines.append('')
        lines.append('| Skill | 必需读取 | 实际读取 | 必需命中 | Recall | Precision |')
        lines.append('|---|---|---|---|---|---|')
        for name, s in sorted(l1['per_skill'].items()):
            lines.append(f"| {name} | {s['expected']} | {s['fired']} | {s['correct']} | "
                         f"{_fmt(s.get('recall'))} | {_fmt(s.get('precision'))} |")
        if l1.get('confusion_pairs'):
            lines.append('')
            lines.append('高频混淆对:' + ';'.join(f'{k}×{v}' for k, v in
                                                  sorted(l1['confusion_pairs'].items(),
                                                         key=lambda kv: -kv[1])[:5]) + '。')
        lines.append('')
    l2 = (report.get('l2') or {}).get('aggregate')
    if l2:
        lines.append('## L2 端到端(隐藏测试)')
        lines.append('')
        lines.append('| 条件 | 运行 | 宏观通过率 | 全过运行数 | pass^k | token 均值 | 秒均值 | 调用率 |')
        lines.append('|---|---|---|---|---|---|---|---|')
        for cond, m in sorted(l2.get('conditions', {}).items()):
            lines.append(f"| {cond} | {m['n_runs']} | {m['mean_partial']} | {m['full_pass_runs']} | "
                         f"{'是' if m['pass_cap_k'] else '否'} | {m['tokens_mean']} | "
                         f"{m['seconds_mean']} | {_fmt(m.get('invocation_rate'))} |")
        fvb = l2.get('full_vs_baseline')
        if fvb:
            lines.append('')
            lines.append(f"full−baseline 宏观差:{fvb['macro_delta']};token 比 "
                         f"{_fmt(fvb.get('token_ratio'))};每请求 input 开销 "
                         f"{_fmt(fvb.get('input_overhead'))}(比值 {_fmt(fvb.get('input_ratio'))});逐任务增益 "
                         + ', '.join(f"{t}:{_fmt(g)}" for t, g in sorted(fvb['normalized_gain_per_task'].items())))
        directed = l2.get('conditions', {}).get('directed')
        if directed:
            lines.append('')
            lines.append(f"directed(被引导使用):宏观通过率 {directed['mean_partial']},"
                         f"skill 调用率 {_fmt(directed.get('invocation_rate'))},"
                         f"全过 {directed['full_pass_runs']}/{directed['n_runs']}。"
                         f"与 organic full 的差异即「引导带来的行为改变」。")
        lines.append('')
    l3 = report.get('l3') or {}
    if l3:
        agg = l3.get('aggregate') or {}
        lines.append('## L3 过程质量')
        lines.append('')
        lines.append(f"槽位 {agg.get('n_slots')};编造声明 {agg.get('fabricated_claims')};"
                     f"追溯覆盖均值 {_fmt(agg.get('traceability_mean'))};"
                     f"最大可见/隐藏差距 {_fmt(agg.get('max_gap'))};"
                     f"歧义词命中 {agg.get('ambiguity_total')};"
                     f"结果枚举出现率 {_fmt(agg.get('outcome_discipline'))}。")
        rg = agg.get('red_green')
        if rg:
            lines.append(f"RED/GREEN 证据文件:{rg['red_files']}(含失败标记 "
                         f"{rg['red_with_failure_marker']})/{rg['green_files']};"
                         f"文件存在不等于真实行为 RED,原始文件可复核。")
        if agg.get('fabricated_slots'):
            lines.append('- 编造槽位:' + ', '.join(f"{s['task']}/{s['condition']}/{s['trial']}"
                                                    for s in agg['fabricated_slots']))
        if agg.get('reward_hack_slots'):
            lines.append('- 差距疑点:' + ', '.join(f"{s['task']}/{s['condition']}/{s['trial']}"
                                                    for s in agg['reward_hack_slots']))
        if l3.get('judge'):
            lines.append('- LLM judge(单裁判,有偏差):' + '; '.join(
                f"{s['task']}/{s['slot']}={s['score']}" if s['score'] else f"{s['task']}/{s['slot']}=解析失败"
                for s in l3['judge']))
        lines.append('')
    diff = report.get('comparison')
    if diff:
        lines.append('## 与验收基线对比')
        lines.append('')
        lines.append(f"- 基线运行:{diff.get('previous_run_id')}")
        if diff.get('gates_regressed'):
            lines.append('- 门回退:' + ', '.join(diff['gates_regressed']))
        if diff.get('gates_recovered'):
            lines.append('- 门恢复:' + ', '.join(diff['gates_recovered']))
        for cond, d in sorted((diff.get('l2_conditions') or {}).items()):
            lines.append(f"- L2 {cond}:{d['mean_partial'][0]} → {d['mean_partial'][1]}(Δ{d['delta']})")
        if not (diff.get('gates_regressed') or diff.get('gates_recovered') or diff.get('l2_conditions')):
            lines.append('- 无门变化。')
        lines.append('')
    lines.append('## 优化方向')
    lines.append('')
    for hint in report.get('optimization_hints', []):
        lines.append(f'- {hint}')
    lines.append('')
    return '\n'.join(lines)


def write_report(run_dir, report):
    run_dir = Path(run_dir)
    (run_dir / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                         encoding='utf-8')
    (run_dir / 'report.md').write_text(render_markdown(report), encoding='utf-8')
    return run_dir / 'report.md'


def finalize(report, run_dir):
    report['optimization_hints'] = optimization_hints(report)
    previous = load_accepted_report(exclude_run_id=report['run_id'])
    report['comparison'] = compare.diff_reports(report, previous)
    path = write_report(run_dir, report)
    upsert_run({'run_id': report['run_id'], 'created_utc': report.get('created_utc'),
                'profile': report.get('profile'), 'status': 'complete',
                'suite_snapshot': (report.get('manifest') or {}).get('snapshot_hash'),
                'accepted': False})
    return path
