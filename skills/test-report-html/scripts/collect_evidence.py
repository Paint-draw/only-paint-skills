#!/usr/bin/env python3
"""扫描项目里的测试证据，汇总成 evidence.json。

报告里的每个数字都要能追回一份报告文件，这个脚本负责把「文件 → 数字」这层做实。

用法：
    python collect_evidence.py --project .                 # 写 test/evidence.json
    python collect_evidence.py --project . --strict        # 有失败时退出码 1
    python collect_evidence.py --project . --include "**/reports/*.xml"

认得的证据：
    Maven      <module>/target/surefire-reports/TEST-*.xml
    Gradle     <module>/build/test-results/**/TEST-*.xml
    pytest 等  test-results/**/*.xml、junit*.xml
    自定义运行  test/results/*.json（harness.py / smoke_matrix.py 的产物）

计数口径：**只数 <testcase> 元素**。JUnit 的 <testsuite tests="N"> 在 @Nested
用例上会少报，用属性计数会得出「绿了」的假结论。
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

PATTERNS = [
    ("maven-surefire", "**/target/surefire-reports/TEST-*.xml"),
    ("gradle", "**/build/test-results/**/TEST-*.xml"),
    ("junit-xml", "**/test-results/**/*.xml"),
    ("junit-xml", "**/junit*.xml"),
]
# 注意：target/ 与 build/ 不能跳——Maven/Gradle 的报告就在里面
SKIP_DIRS = {".git", "node_modules", "dist", ".venv", "venv", "__pycache__"}


def localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def count_testcases(root: ET.Element) -> dict:
    tests = failures = errors = skipped = 0
    classes: dict[str, int] = {}
    for case in root.iter():
        if localname(case.tag) != "testcase":
            continue
        tests += 1
        cls = case.get("classname") or case.get("name") or "(unknown)"
        classes[cls] = classes.get(cls, 0) + 1
        for child in case:
            kind = localname(child.tag)
            if kind == "failure":
                failures += 1
            elif kind == "error":
                errors += 1
            elif kind == "skipped":
                skipped += 1
    return {"tests": tests, "failures": failures, "errors": errors,
            "skipped": skipped, "classes": classes}


def module_of(rel: Path) -> str:
    """取 target/ 或 build/ 前面那一段当模块名。"""
    parts = rel.parts
    for i, part in enumerate(parts):
        if part in ("target", "build") and i > 0:
            return parts[i - 1]
    return parts[0] if len(parts) > 1 else "root"


def scan(project: Path, includes: list[str]) -> tuple[list[dict], list[dict], dict | None, list[str]]:
    files: dict[str, dict] = {}
    runs: list[dict] = []
    coverage: dict | None = None
    warnings: list[str] = []

    patterns = list(PATTERNS) + [("custom", p) for p in includes]
    for framework, pattern in patterns:
        for hit in glob.glob(str(project / pattern), recursive=True, include_hidden=False):
            path = Path(hit).resolve()
            if any(part in SKIP_DIRS for part in path.relative_to(project).parts[:-1]):
                continue
            key = str(path)
            if key in files:
                continue
            if path.suffix == ".json":
                continue
            try:
                root = ET.parse(path).getroot()
            except ET.ParseError as exc:
                warnings.append(f"跳过无法解析的报告 {path.relative_to(project)}: {exc}")
                continue
            counts = count_testcases(root)
            rel = path.relative_to(project)
            files[key] = {
                "path": rel.as_posix(),
                "framework": framework,
                "module": module_of(rel),
                "mtime": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
                **counts,
            }

    results_dir = project / "test" / "results"
    for path in sorted(results_dir.glob("*.json")) if results_dir.exists() else []:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"跳过无法解析的结果 {path.name}: {exc}")
            continue
        kind = "e2e" if isinstance(data, list) else data.get("kind", "e2e")
        # 覆盖统计不是业务闭环：它没有 items，也不进 runs，
        # 否则「端到端 N 条」会被一条汇总 JSON 抬走。必须在 items 判空**之前**分流。
        if kind == "coverage":
            coverage = {**data, "path": path.relative_to(project).as_posix()}
            continue
        items = data if isinstance(data, list) else (
            data.get("items") or data.get("flows") or data.get("runs") or [])
        if not items:
            continue
        failed = sum(1 for i in items if str(i.get("status", "")).upper() not in ("PASS", "OK", "SKIP"))
        runs.append({
            "name": path.stem,
            "path": path.relative_to(project).as_posix(),
            "kind": kind,
            "count": len(items),
            "failed": failed,
            "mtime": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
            # 顶层标量原样带出来，报告里才能用 {{run.<name>.<字段>}} 引用自定义读数
            **{k: v for k, v in data.items()
               if not isinstance(v, (list, dict)) and k not in ("name", "path", "kind")},
            "items": items,
        })

    return list(files.values()), runs, coverage, warnings


def mark_stale(files: list[dict], hours: int) -> list[dict]:
    """找出「本轮大概率没跑」的报告文件。

    判据取**本次扫描到的最新 mtime**作基准：同一批报告里，比它早 N 小时以上的，
    多半是上一轮留下、这次没被覆盖的残留（已删测试类的产物就是这样混进来的）。
    只认「同批里明显偏旧」，不针对单个文件——单个且旧的情况由 --max-age-days 管。
    """
    if len(files) < 2:
        return []
    newest = max(datetime.fromisoformat(f["mtime"]) for f in files)
    cutoff = newest - timedelta(hours=hours)
    stale = []
    for f in files:
        mtime = datetime.fromisoformat(f["mtime"])
        if mtime < cutoff:
            gap = newest - mtime
            stale.append({
                "path": f["path"],
                "mtime": f["mtime"],
                "reason": f"比本轮最新报告早 {gap.days} 天 {gap.seconds // 3600} 小时",
            })
    return stale


def summarize(files: list[dict], runs: list[dict], coverage: dict | None = None) -> dict:
    total = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    modules: dict[str, dict] = {}
    for f in files:
        for k in total:
            total[k] += f[k]
        m = modules.setdefault(f["module"], {
            "name": f["module"], "tests": 0, "failures": 0, "errors": 0,
            "skipped": 0, "classes": 0, "files": 0,
            "frameworks": set(), "newest": "",
        })
        for k in ("tests", "failures", "errors", "skipped"):
            m[k] += f[k]
        m["classes"] += len(f["classes"])
        m["files"] += 1
        m["frameworks"].add(f["framework"])
        m["newest"] = max(m["newest"], f["mtime"])
    for m in modules.values():
        m["frameworks"] = sorted(m["frameworks"])
    total["files"] = len(files)
    total["classes"] = sum(m["classes"] for m in modules.values())
    e2e = [r for r in runs if r["kind"] != "matrix"]
    matrix = [r for r in runs if r["kind"] == "matrix"]
    return {
        "total": total,
        "modules": sorted(modules.values(), key=lambda m: -m["tests"]),
        "runs_total": {
            "count": sum(r["count"] for r in e2e),
            "failed": sum(r["failed"] for r in e2e),
            "files": len(e2e),
        },
        # 接口矩阵是「端点 × 角色」的调用次数，不能和业务闭环混着数
        "matrix_total": {
            "calls": sum(r["count"] for r in matrix),
            "problems": sum(r["failed"] for r in matrix),
            "files": len(matrix),
        },
        "negative": summarize_negative(coverage),
    }


def summarize_negative(coverage: dict | None) -> dict | None:
    """覆盖统计。没登记就返回 None —— 报告里要显示「未统计」，不能显示 0。

    0 会被读成「一条负向用例都没有」，那是完全不同的结论。
    """
    if not coverage:
        return None
    missing = coverage.get("files_without_negative") or []
    return {
        "method": coverage.get("method", "unknown"),
        "method_note": coverage.get("method_note", ""),
        "negative": coverage.get("negative"),
        "boundary": coverage.get("boundary"),
        "total_cases": coverage.get("total_cases"),
        "files_scanned": coverage.get("files_scanned"),
        "files_without_negative": len(missing),
        "files_without_negative_sample": missing[:5],
        "source": coverage.get("path", ""),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".", help="项目根目录")
    ap.add_argument("--out", default="test/evidence.json")
    ap.add_argument("--include", action="append", default=[],
                    help="额外的报告 glob（可重复）")
    ap.add_argument("--max-age-days", type=int, default=7,
                    help="证据比这更旧就告警")
    ap.add_argument("--stale-after-hours", type=int, default=24,
                    help="比本轮最新报告早这么多小时的，判为疑似残留")
    ap.add_argument("--exclude-stale", action="store_true",
                    help="把疑似残留从统计里剔除（默认仍计入）")
    ap.add_argument("--strict", action="store_true", help="有失败/报错时退出码 1")
    args = ap.parse_args()

    project = Path(args.project).resolve()
    files, runs, coverage, warnings = scan(project, args.include)
    stale = mark_stale(files, args.stale_after_hours)
    if stale:
        warnings.append(
            f"{len(stale)} 份报告疑似本轮未运行（比最新报告早 {args.stale_after_hours} 小时以上）"
            f"，会把用例数抬高；确认是残留就清掉，或加 --exclude-stale。")
        if args.exclude_stale:
            stale_paths = {s["path"] for s in stale}
            files = [f for f in files if f["path"] not in stale_paths]
    summary = summarize(files, runs, coverage)

    if not files and not runs:
        warnings.append("没有找到任何测试证据；报告里的数字将无从追溯。")
    newest = max((f["mtime"] for f in files), default="")
    if newest:
        age = (datetime.now() - datetime.fromisoformat(newest)).days
        if age > args.max_age_days:
            warnings.append(f"最新一份测试报告已是 {age} 天前，先重跑测试再出报告。")
    if summary["total"]["failures"] or summary["total"]["errors"]:
        warnings.append("存在失败或报错的用例，报告里不能写「全部通过」。")
    if summary["runs_total"]["failed"]:
        warnings.append(f"端到端有 {summary['runs_total']['failed']} 条 FAIL。")
    if summary["matrix_total"]["problems"]:
        warnings.append(f"接口矩阵有 {summary['matrix_total']['problems']} 个非权限类异常。")

    evidence = {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "project": str(project),
        **summary,
        "test_reports": {"files": files, "stale": stale},
        "runs": runs,
        "warnings": warnings,
    }

    out = project / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")

    t = summary["total"]
    print(f"自动化：{t['tests']} 条 / {t['files']} 份报告，失败 {t['failures']}，报错 {t['errors']}，跳过 {t['skipped']}")
    for m in summary["modules"]:
        print(f"  {m['name']:20s} {m['tests']:5d} 条  {m['classes']:3d} 类  {'/'.join(m['frameworks'])}")
    rt = summary["runs_total"]
    print(f"端到端：{rt['files']} 份，{rt['count']} 条，FAIL {rt['failed']}")
    mt = summary["matrix_total"]
    print(f"接口矩阵：{mt['files']} 份，{mt['calls']} 次调用，异常 {mt['problems']}")
    for r in runs:
        print(f"  {r['name']:24s} {r['kind']:6s} {r['count']:4d} 条  FAIL {r['failed']}")
    neg = summary.get("negative")
    if neg:
        print(f"覆盖统计：负向 {neg['negative']} 条 / 边界 {neg['boundary']} 条"
              f"（口径 {neg['method']}：{neg['method_note'] or '—'}）")
    else:
        print("覆盖统计：未登记（report.json 里用 quality 块会显示「未统计」）")
    for s in stale:
        print(f"  疑似残留 {s['path']}（{s['reason']}）")
    for w in warnings:
        print(f"⚠ {w}")
    print(f"\n已写 {out.relative_to(project).as_posix() if out.is_relative_to(project) else out}")

    bad = t["failures"] or t["errors"] or rt["failed"]
    return 1 if (args.strict and bad) else 0


if __name__ == "__main__":
    sys.exit(main())
