#!/usr/bin/env python3
"""SDD Workbench 三层评测与验收回归入口。

典型用法:
  python3 evals/regression/run.py --probe                 # 单槽位验证事件解析
  python3 evals/regression/run.py --profile smoke         # 冒烟(2 次运行)
  python3 evals/regression/run.py --profile standard      # 全量(L1+L2+L3)
  python3 evals/regression/run.py --accept <run_id>       # 把某次运行定为验收基线
产物只写入 .eval-artifacts/regression/(可用 SDD_REGRESSION_ARTIFACTS 重定向),
绝不安装或修改任何线上 skill。模型固定为显式 DeepSeek Flash,身份按运行记录。
"""
import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from runner import compare, l1_trigger, l2_e2e, l3_process, pi_runner
from runner import reporting as report_mod
from runner import runtime as runtime_mod
from runner.paths import runs_root, suite_skills
from runner.slots import Slots, run_parallel

PROFILES = {
    'smoke': {'l1_limit': 0, 'l2_tasks': 1, 'l2_conditions': ['baseline', 'full'], 'trials': 1},
    'quick': {'l1_limit': 30, 'l2_tasks': 2, 'l2_conditions': ['baseline', 'full'], 'trials': 2},
    'standard': {'l1_limit': None, 'l2_tasks': None, 'l2_conditions': None, 'trials': 3},
    'full': {'l1_limit': None, 'l2_tasks': None, 'l2_conditions': None, 'trials': 3, 'loo': True},
}


def _git(*args):
    return subprocess.check_output(['git', *args], cwd=Path(__file__).resolve().parents[2],
                                   text=True).strip()


def freeze_ref(suite_ref):
    """'worktree' freezes the uncommitted working tree; anything else is a git ref."""
    return None if suite_ref == 'worktree' else suite_ref


def build_slots(slots, profile, tasks, conditions, layer='all'):
    if layer in ('l1', 'all') and (profile['l1_limit'] is None or profile['l1_limit'] > 0):
        cases = l1_trigger.load_cases()
        if profile['l1_limit']:
            cases = cases[:profile['l1_limit']]
        for case in cases:
            slots.add({'id': 'l1:' + case['id'], 'kind': 'l1', 'case': case, 'timeout': 600})
    if layer in ('l2', 'all'):
        allowed = profile['l2_conditions']
        conds = [c for c in conditions if allowed is None or c['id'] in allowed]
        for task in tasks[:profile['l2_tasks'] or None]:
            for cond in conds:
                for trial in range(1, profile['trials'] + 1):
                    slots.add({'id': f"l2:{task['id']}:{cond['id']}:t{trial}", 'kind': 'l2',
                               'task': task, 'condition': cond, 'trial': trial,
                               'timeout': task['timeout']})


def make_worker(slots, run_dir, runtime_full, executable):
    def worker(slot):
        if slot['kind'] == 'l1':
            l1_trigger.execute_slot(slot, run_dir, runtime_full, executable)
        else:
            l2_e2e.execute_slot(slot, run_dir, runtime_full, executable)
        slots.mark(slot['id'], 'done')
    return worker


def collect(run_dir, conditions, args, manifest):
    report = {'run_id': manifest['run_id'], 'created_utc': manifest['created_utc'],
              'profile': args.profile, 'manifest': manifest}
    l1_results = [json.loads(p.read_text(encoding='utf-8'))
                  for p in sorted(Path(run_dir).glob('l1/*/result.json'))]
    report['l1'] = ({'aggregate': l1_trigger.aggregate(l1_results), 'n_cases': len(l1_results)}
                    if l1_results else None)
    l2_results = [json.loads(p.read_text(encoding='utf-8'))
                  for p in sorted(Path(run_dir).glob('l2/*/*/t*/result.json'))]
    l2_agg = l2_e2e.aggregate(l2_results, conditions) if l2_results else {}
    fvb = l2_agg.get('full_vs_baseline') or {}
    dvb = l2_agg.get('directed_vs_baseline') or {}
    l2_flat = dict(l2_agg)
    l2_flat.update({'full_minus_baseline_macro': fvb.get('macro_delta'),
                    'gain_nonneg_task_fraction': fvb.get('gain_nonneg_task_fraction'),
                    'worst_task_delta': fvb.get('worst_task_delta'),
                    'full_over_baseline_token_ratio': fvb.get('token_ratio'),
                    'directed_invocation': dvb.get('invocation_rate'),
                    'directed_minus_baseline_macro': dvb.get('macro_delta'),
                    'directed_over_baseline_token_ratio': dvb.get('token_ratio')})
    report['l2'] = {'aggregate': l2_agg} if l2_results else None
    checks = l3_process.collect(run_dir)
    report['l3'] = {'aggregate': l3_process.aggregate(checks)} if checks else None
    if args.judge and l2_results:
        report['l3']['judge'] = l3_process.judge(run_dir, l2_e2e.load_tasks(),
                                                 executable=args.executable)
    metrics = {'l1': (report['l1'] or {}).get('aggregate'),
               'l2': l2_flat if l2_results else None,
               'l3': (report['l3'] or {}).get('aggregate')}
    report['gates'] = compare.evaluate_gates(metrics)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=sorted(PROFILES), default='standard')
    parser.add_argument('--suite-ref', default='HEAD')
    parser.add_argument('--layer', choices=['l1', 'l2', 'l3', 'all'], default='all')
    parser.add_argument('--ablate', action='append', metavar='SKILL',
                        help='附加 leave-one-out 条件,如 --ablate sdd-plan-slices')
    parser.add_argument('--max-parallel', type=int, default=3)
    parser.add_argument('--executable', default='pi')
    parser.add_argument('--judge', action='store_true', help='L3 附加单裁判 LLM 打分')
    parser.add_argument('--retry-errors', action='store_true',
                        help='把 error 槽位重新置为 pending 后再执行')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--probe', action='store_true')
    parser.add_argument('--run-dir', help='重入既有运行目录(配合 --layer l3/报告重生成)')
    parser.add_argument('--accept', metavar='RUN_ID', help='将运行标记为验收基线(显式人工动作)')
    args = parser.parse_args()

    if args.accept:
        report_mod.accept(args.accept)
        print(f"已将 {args.accept} 标记为验收基线。")
        return

    if args.run_dir:
        run_dir = Path(args.run_dir)
        if not run_dir.is_dir():
            parser.error(f'run dir 不存在: {run_dir}')
        manifest = json.loads((run_dir / 'manifest.json').read_text(encoding='utf-8'))
    else:
        run_id = (datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
                  + '-' + args.profile)
        run_dir = runs_root() / run_id
        if run_dir.exists():
            parser.error(f'运行目录已存在: {run_dir}')
        run_dir.mkdir(parents=True)
        revision = _git('rev-parse', ('HEAD' if args.suite_ref == 'worktree'
                                      else args.suite_ref) + '^{commit}')
        manifest = {'run_id': run_id,
                    'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'profile': args.profile, 'suite_ref': args.suite_ref,
                    'revision': revision,
                    'dirty': bool(_git('status', '--porcelain')),
                    'harness_argv': sys.argv[1:]}
        (run_dir / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                               encoding='utf-8')

    if args.probe:
        _probe(args, run_dir)
        return

    profile = PROFILES[args.profile]
    tasks = l2_e2e.load_tasks()
    extra_ablate = list(args.ablate or [])
    if profile.get('loo') and not args.run_dir:
        extra_ablate += list(suite_skills())
    conditions = l2_e2e.load_conditions(extra_ablate=extra_ablate)
    slots = Slots(run_dir / 'slots.json')
    build_slots(slots, profile, tasks, conditions, layer=args.layer)
    pending = slots.pending()
    print(f"运行目录:{run_dir}")
    print(f"槽位:总 {len(slots.all())},待执行 {len(pending)}(L1={sum(1 for s in slots.all() if s['kind'] == 'l1')},"
          f"L2={sum(1 for s in slots.all() if s['kind'] == 'l2')})")
    if args.dry_run:
        for slot in slots.all():
            print(f"  {slot['id']}  {slot['status']}")
        return

    runtime_full = run_dir / 'runtime-full'
    needs_runtime = any(s['kind'] == 'l1' or s['condition']['skills'] for s in slots.all())
    if needs_runtime:
        if not runtime_full.exists():
            info = runtime_mod.freeze(runtime_full,
                                      ref=freeze_ref(manifest.get('suite_ref')
                                                     if args.run_dir else args.suite_ref))
            manifest['runtime_source'] = info
        manifest['snapshot_hash'] = runtime_mod.snapshot_hash(runtime_full)['total']
    manifest['pi_environment'] = pi_runner.environment(args.executable)
    manifest['provider_model'] = f'{pi_runner.PROVIDER}/{pi_runner.MODEL}'
    (run_dir / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                           encoding='utf-8')

    if args.retry_errors:
        errored = [s for s in slots.all() if s['status'] == 'error']
        for slot in errored:
            slots.mark(slot['id'], 'pending')
        if errored:
            print(f"--retry-errors:重排 {len(errored)} 个错误槽位")
    pending = slots.pending()
    if pending:
        worker = make_worker(slots, run_dir, runtime_full, args.executable)
        run_parallel(slots, worker, max_workers=args.max_parallel)
        errored = [s for s in slots.all() if s['status'] == 'error']
        print(f"执行完成:错误槽位 {len(errored)}")
        for slot in errored[:10]:
            print(f"  {slot['id']}: {slot.get('detail')}")

    report = collect(run_dir, conditions, args, manifest)
    path = report_mod.finalize(report, run_dir)
    failed = [g for g in report['gates'] if not g['passed'] and not g['missing']]
    print(f"报告:{path}")
    print(f"验收门:{len(report['gates']) - len(failed) - sum(1 for g in report['gates'] if g['missing'])}"
          f"/{len(report['gates'])} 通过;未过:{', '.join(g['id'] for g in failed) or '无'}")
    print("如需定为验收基线:python3 evals/regression/run.py --accept "
          f"{manifest['run_id']}")


def _probe(args, run_dir):
    cases = [c for c in l1_trigger.load_cases() if c['expect']['trigger']]
    case = cases[0]
    runtime_full = run_dir / 'runtime-full'
    if not runtime_full.exists():
        runtime_mod.freeze(runtime_full, ref=freeze_ref(args.suite_ref))
    dest = l1_trigger.prepare(case, run_dir, 600)
    if dest is None:
        dest = l1_trigger.slot_dir(run_dir, case)
    if not (dest / 'process-result.json').exists():
        pi_runner.run(dest, skills_dir=runtime_full, executable=args.executable, timeout=600)
    from runner import events
    parsed = events.parse(dest / 'events.jsonl')
    fired = events.detect_skills(parsed, runtime_full, dest / 'project')
    print(json.dumps({'case': case['id'], 'expected': case['expect']['trigger'], 'fired': fired,
                      'usage_events': parsed['usage']['usage_events'],
                      'reads': len(parsed['reads']),
                      'skill_events': len(parsed['skill_events']),
                      'parse_errors': parsed['parse_errors'],
                      'unknown_types': parsed['unknown_types'],
                      'lines': parsed['lines']}, ensure_ascii=False, indent=2))
    if not fired:
        print('警告:未检测到任何 skill 触发。请人工检查 events.jsonl 中的事件形态,'
              '必要时更新 runner/events.py 的解析规则。')


if __name__ == '__main__':
    main()
