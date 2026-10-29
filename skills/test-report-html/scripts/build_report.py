#!/usr/bin/env python3
"""把 evidence.json（机器读数）与 report.json（人的叙事）渲染成单文件 HTML 报告。

为什么分两段：读数会过期，叙事不会。数字一律用 {{占位符}} 从证据里取，
报告交出去之后别人还能顺着页脚的证据清单追到原始文件。

用法：
    python build_report.py --project .                    # 写 docs/internal-test-report.html
    python build_report.py --project . --out test/report.html
    python build_report.py --project . --check            # 只校验不写

可用占位符：
    {{tests.total}} {{tests.failures}} {{tests.errors}} {{tests.skipped}} {{tests.files}} {{tests.classes}}
    {{modules.count}} {{modules.<模块名>.tests}} {{modules.<模块名>.classes}}
    {{runs.count}} {{runs.failed}} {{runs.files}}
    {{matrix.calls}} {{matrix.problems}} {{matrix.files}}
    {{generated_at}}
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
TOKEN = re.compile(r"\{\{\s*([a-zA-Z0-9_.\-]+)\s*\}\}")
CODE_ID = re.compile(r"^[A-Z]{1,2}\d{2}$")


def load(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"缺少文件：{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def resolve(evidence: dict, key: str):
    parts = key.split(".")
    if parts[0] == "tests":
        field = "tests" if parts[1] == "total" else parts[1]
        return evidence.get("total", {}).get(field)
    if parts[0] == "runs":
        return evidence.get("runs_total", {}).get(parts[1])
    if parts[0] == "matrix":
        return evidence.get("matrix_total", {}).get(parts[1])
    if parts[0] == "generated_at":
        return evidence.get("generated_at")
    if parts[0] == "modules":
        if parts[1] == "count":
            return len(evidence.get("modules", []))
        for m in evidence.get("modules", []):
            if m["name"] == parts[1] and len(parts) > 2:
                return m.get(parts[2])
    return None


def fill(text: str, evidence: dict, missing: list[str], where: str) -> str:
    def sub(match):
        value = resolve(evidence, match.group(1))
        if value is None:
            missing.append(f"{where}: {{{{{match.group(1)}}}}}")
            return match.group(0)
        return str(value)

    return TOKEN.sub(sub, text)


def render_table(block: dict, evidence: dict, missing: list[str], where: str) -> str:
    head = "".join(f"<th>{c}</th>" for c in block.get("headers", []))
    rows = []
    for row in block.get("rows", []):
        cells = []
        for i, cell in enumerate(row):
            cls = ' class="code"' if i == 0 and CODE_ID.match(str(cell)) else ""
            cells.append(f"<td{cls}>{fill(str(cell), evidence, missing, where)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    title = f"<h3>{fill(block['title'], evidence, missing, where)}</h3>" if block.get("title") else ""
    return f"{title}<table><tr>{head}</tr>{''.join(rows)}</table>"


def render_block(block: dict, evidence: dict, missing: list[str], where: str) -> str:
    kind = block.get("type", "paragraph")
    if kind == "table":
        return render_table(block, evidence, missing, where)
    if kind == "bullets":
        items = "".join(f"<li>{fill(i, evidence, missing, where)}</li>" for i in block.get("items", []))
        title = f"<h3>{fill(block['title'], evidence, missing, where)}</h3>" if block.get("title") else ""
        return f"{title}<ul>{items}</ul>"
    if kind == "note":
        return f"<div class=\"note\">{fill(block.get('text', ''), evidence, missing, where)}</div>"
    return f"<p>{fill(block.get('text', ''), evidence, missing, where)}</p>"


def render_section(section: dict, evidence: dict, missing: list[str]) -> str:
    no, title = section.get("no", ""), section.get("title", "")
    where = f"{no} {title}"
    parts = [f'<h2><span class="no">{no}</span>{title}</h2>']
    if section.get("lead"):
        parts.append(f'<p class="lead">{fill(section["lead"], evidence, missing, where)}</p>')
    if section.get("columns"):
        cols = []
        for col in section["columns"]:
            cols.append("".join(render_block(b, evidence, missing, where) for b in col))
        parts.append('<div class="two">' + "".join(f"<div>{c}</div>" for c in cols) + "</div>")
    for block in section.get("blocks", []):
        parts.append(render_block(block, evidence, missing, where))
    return "<section>" + "".join(parts) + "</section>"


def render_cards(cards: list[dict], evidence: dict, missing: list[str]) -> tuple[str, list[str]]:
    """卡片数字必须来自证据；手写数字要写明出处，否则拒绝出报告。"""
    literals: list[str] = []
    out = []
    for i, card in enumerate(cards, 1):
        raw = str(card.get("value", ""))
        where = f"卡片{i}「{card.get('label', '')}」"
        if "{{" not in raw and raw.strip().isdigit():
            source = card.get("source")
            if not source:
                raise SystemExit(
                    f"{where} 用的是手写数字 {raw}，但没有 source。\n"
                    "请改成 {{...}} 占位符，或在卡片上加 \"source\": \"读数出处\"。")
            literals.append(f"{where} = {raw}（{source}）")
        value = fill(raw, evidence, missing, where)
        style = card.get("style", "")
        cls = f"card {style}".strip()
        out.append(f'<div class="{cls}"><b>{value}</b><span>{card.get("label", "")}</span></div>')
    return f'<div class="cards">{"".join(out)}</div>', literals


def render_evidence(evidence: dict) -> str:
    rows = []
    for f in evidence.get("test_reports", {}).get("files", []):
        rows.append(
            f"<tr><td>{html.escape(f['path'])}</td><td>{f['framework']}</td>"
            f"<td>{f['tests']}</td><td>{f['failures'] + f['errors']}</td>"
            f"<td>{html.escape(f['mtime'])}</td></tr>")
    run_rows = []
    for r in evidence.get("runs", []):
        run_rows.append(
            f"<tr><td>{html.escape(r['path'])}</td><td>{r['count']}</td>"
            f"<td>{r['failed']}</td><td>{html.escape(r['mtime'])}</td></tr>")
    files_table = (
        "<table><tr><th>报告文件</th><th>框架</th><th>用例</th><th>失败</th><th>生成时间</th></tr>"
        + "".join(rows) + "</table>") if rows else "<p>没有自动化报告文件。</p>"
    runs_table = (
        "<table><tr><th>运行结果</th><th>条数</th><th>FAIL</th><th>生成时间</th></tr>"
        + "".join(run_rows) + "</table>") if run_rows else "<p>没有运行时结果文件。</p>"
    return (
        '<details class="evidence"><summary>读数来源（每个数字都能追到这里）</summary>'
        f"<p>证据汇总生成于 {html.escape(str(evidence.get('generated_at')))}</p>"
        f"{files_table}{runs_table}</details>")


def build(project: Path, report: dict, evidence: dict) -> str:
    missing: list[str] = []
    css = (ASSETS / "report.css").read_text(encoding="utf-8")

    cards_html, literals = render_cards(report.get("cards", []), evidence, missing)

    title = report.get("title", "测试报告")
    title_html = "<br />".join(title) if isinstance(title, list) else title
    meta = "".join(f"<span>{fill(m, evidence, missing, '页头')}</span>" for m in report.get("meta", []))
    hero = (
        f'<div class="hero"><div class="eyebrow">{report.get("eyebrow", "")}</div>'
        f"<h1>{title_html}</h1><p>{fill(report.get('summary', ''), evidence, missing, '页头')}</p>"
        f'<div class="meta">{meta}</div></div>')

    sections = "".join(render_section(s, evidence, missing) for s in report.get("sections", []))

    if missing:
        raise SystemExit("以下占位符在证据里找不到值，报告未生成：\n  " + "\n  ".join(missing))

    extra = ""
    if literals:
        extra = ('<details class="evidence"><summary>人工读数（手写数字及其出处）</summary><ul>'
                 + "".join(f"<li>{html.escape(x)}</li>" for x in literals) + "</ul></details>")

    return (
        "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"UTF-8\" />\n"
        '<meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
        f"<title>{title_html.replace('<br />', ' · ')}</title>\n<style>\n{css}</style>\n</head>\n<body>\n"
        f'<div class="page">\n{hero}\n{cards_html}\n{sections}\n{extra}{render_evidence(evidence)}\n'
        f'<div class="footer">{report.get("footer", "")}</div>\n</div>\n</body>\n</html>\n')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--evidence", default="test/evidence.json")
    ap.add_argument("--report", default="test/report.json")
    ap.add_argument("--out", default="")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    project = Path(args.project).resolve()
    evidence = load(project / args.evidence)
    report = load(project / args.report)
    content = build(project, report, evidence)

    out = Path(args.out) if args.out else (
        project / "docs" / "internal-test-report.html"
        if (project / "docs").is_dir() else project / "test" / "report.html")
    if args.check:
        print(f"校验通过：{len(content)} 字符，{len(evidence.get('test_reports', {}).get('files', []))} 份报告文件")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    print(f"已生成 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
