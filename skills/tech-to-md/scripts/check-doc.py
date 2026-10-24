#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""技术实现文档的机械自检。

用法：
    python check-doc.py <文档.md> [--strict]

检查两类东西：
  1. 必备结构（一页概览 / 已知的粗糙处 / 被否掉的方案 / 行为变更）；
  2. 体例明令禁写的内容（日期、提交 sha、交付读数、台账指针……）与可疑措辞。

它只做机械项，不判断内容是否讲透——那靠 references/自查清单.md 与口述验收。

退出码：有 ERROR ⇒ 1；只有 WARN ⇒ 0（--strict 时 ⇒ 1）。
局部豁免：在目标行的上一行写 <!-- check-doc: ignore-next-line -->
"""

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- 规则定义

# (名称, 正则, 说明)
REQUIRED_HEADINGS = [
    ("一页概览", r"^#{1,3}\s*.*一页概览", "缺少「〇、一页概览」——读者无法在一屏内建立整条链路"),
    ("已知的粗糙处", r"^#{1,3}\s*.*已知的粗糙处", "缺少「已知的粗糙处」——地图会过期"),
    ("被否掉的方案", r"^#{1,3}\s*.*被否掉的方案", "缺少「被否掉的方案」——设计理由少了承重半边"),
    ("行为变更", r"^#{1,3}\s*.*行为变更", "缺少「行为变更」——契约可比性没有入账"),
]

FORBIDDEN = [
    ("日期锚", r"20\d{2}\s*[-/年]\s*\d{1,2}\s*[-/月]\s*\d{1,2}",
     "技术文档不写日期锚；它属于 git log / 台账"),
    ("提交 sha", r"(?:提交|commit|Commit|sha|SHA)[^\n]{0,30}\b[0-9a-f]{7,40}\b",
     "技术文档不写提交 sha；它属于台账"),
    ("交付状态", r"已上线|已部署|已过验收|已通过验收|已验收|已发布",
     "技术文档不写交付状态；它属于台账"),
    ("部署动作", r"pm2\s+reload|pm_uptime",
     "技术文档不写部署动作与时间戳；它属于台账"),
    ("测试计数沿革",
     r"(?:测试|用例|test)[^\n]{0,24}\d+\s*(?:→|->)\s*\d+|\d+\s*(?:→|->)\s*\d+\s*(?:条|个)?\s*(?:测试|用例)",
     "技术文档不写测试计数沿革；它属于台账"),
    ("台账编号", r"(?<![A-Za-z0-9_])N\d{3}(?![A-Za-z0-9_])",
     "技术文档不写台账编号；改为直接引用节号或符号名"),
    # 注意：「本轮 / 本次」在技术正文里有合法用法（如「该键本轮第一次请求」「本次返回的行数」），
    # 只有后面跟开发批次语义时才算禁写项。
    ("批次词", r"本批|收口态|（最新）|(?:本轮|本次)\s*(?:批次|工作|改造|修复|交付|验收|实施|上线|发布|变更|迭代|需求|计划)",
     "技术文档不写开发批次与「最新」；写法应时间无关"),
]

WARNINGS = [
    ("单星标记", r"(?<!★)★(?!★)",
     "只允许 ★★ 标承重点，单 ★ 请去掉"),
    ("索引表写死数量", r"共\s*\d+\s*个",
     "索引表只列 # / 主题 / 位置，不写数量"),
    ("模糊措辞", r"我们认为|我认为|应该是",
     "要么给证据，要么写「推断 / 未核」"),
]

ANCHOR_WITH_LINE = re.compile(r"(?:\.(?:py|ts|tsx|js|jsx|java|go|rs|rb|php|cs|kt|scala)):\d+|::[^\s:：]+:\d+")
EXTRACT_POINT_DECLARED = re.compile(r"抽取点|行号.*漂|会漂")
IGNORE_MARK = "check-doc: ignore-next-line"


# ---------------------------------------------------------------- 主流程

def read_lines(path: Path):
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    return text.splitlines()


def main() -> int:
    parser = argparse.ArgumentParser(description="技术实现文档机械自检")
    parser.add_argument("doc", help="目标 Markdown 文件")
    parser.add_argument("--strict", action="store_true", help="出现 WARN 也返回非零")
    args = parser.parse_args()

    path = Path(args.doc)
    if not path.is_file():
        print(f"ERROR 找不到文件：{path}")
        return 2

    lines = read_lines(path)
    errors = []
    warns = []

    def is_ignored(idx: int) -> bool:
        return idx > 0 and IGNORE_MARK in lines[idx - 1]

    # 1) 必备结构
    headings = [ln for ln in lines if ln.lstrip().startswith("#")]
    for name, pattern, msg in REQUIRED_HEADINGS:
        if not any(re.search(pattern, h) for h in headings):
            errors.append((0, "必备结构", f"缺少「{name}」：{msg}"))

    # 2) 禁写项
    for idx, line in enumerate(lines):
        if is_ignored(idx):
            continue
        for name, pattern, msg in FORBIDDEN:
            if re.search(pattern, line):
                errors.append((idx + 1, name, f"{msg} ⇒ {line.strip()[:120]}"))

    # 3) 可疑项
    for idx, line in enumerate(lines):
        if is_ignored(idx):
            continue
        for name, pattern, msg in WARNINGS:
            if re.search(pattern, line):
                warns.append((idx + 1, name, f"{msg} ⇒ {line.strip()[:120]}"))

    # 4) 带行号的锚点需声明抽取点
    if any(ANCHOR_WITH_LINE.search(ln) for ln in lines) and not any(
        EXTRACT_POINT_DECLARED.search(ln) for ln in lines
    ):
        for idx, line in enumerate(lines):
            if ANCHOR_WITH_LINE.search(line):
                warns.append((idx + 1, "锚点行号",
                              "带行号的代码锚点未声明抽取点（行号会漂）"))
                break

    # 5) 全文既无「实测」也无「未核」⇒ 证据强度可能没交代
    has_evidence_word = any(("实测" in ln or "未核" in ln) for ln in lines)
    if not has_evidence_word:
        warns.append((0, "证据强度",
                      "全文既无「实测」也无「未核」——请确认证据强度是否已交代"))

    # 6) 输出
    for lineno, rule, msg in errors:
        loc = f"第 {lineno} 行" if lineno else "全文"
        print(f"ERROR [{rule}] {loc}：{msg}")
    for lineno, rule, msg in warns:
        print(f"WARN  [{rule}] 第 {lineno} 行：{msg}")

    print("-" * 60)
    print(f"检查完成：ERROR {len(errors)} 项，WARN {len(warns)} 项 · {path}")
    print("提示：机械项通过 ≠ 内容过关。五要素、设计取舍与口述验收请继续过 references/自查清单.md。")
    if errors:
        return 1
    if warns and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
