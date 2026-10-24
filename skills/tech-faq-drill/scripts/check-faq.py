#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""技术问答库（FAQ）的机械自检。

用法：
    python check-faq.py <FAQ.md> [--strict]

检查的都是「一旦不同步，整个库就不可信」的机械项：
  1. 索引表与正文条目是否一一对应；
  2. Q 号是否重复、是否递增；
  3. 每条是否具备必备字段（模块 / 依据 / 证据强度 / 一句话 / 展开）；
  4. 可疑项：缺「可能被追问」、依据带行号却没声明会漂、全文没有一处「未核」。

它不判断答案好不好——那靠 references/作答体例.md 的念稿自检。

退出码：有 ERROR ⇒ 1；只有 WARN ⇒ 0（--strict 时 ⇒ 1）。
局部豁免：在目标行的上一行写 <!-- check-faq: ignore-next-line -->
"""

import argparse
import re
import sys
from pathlib import Path

INDEX_HEADER = ["#", "问题", "模块", "依据"]
INDEX_HEADING = re.compile(r"^#{2,3}\s*.*索引")
BODY_HEADING = re.compile(r"^##\s*Q(\d+)\s*[.、]")
ANY_HEADING = re.compile(r"^#{1,6}\s")
ROW_NUMBER = re.compile(r"^Q(\d+)$")
SEPARATOR_CELL = re.compile(r"^:?-{2,}:?$")
LINE_NUMBER_IN_ANCHOR = re.compile(
    r"(?:\.(?:py|ts|tsx|js|jsx|java|go|rs|rb|php|cs|kt|scala)|::[^\s:：]+|§[^\s:：]*):\d+"
)
DRIFT_DECLARED = re.compile(r"会漂|行号.*不保证|抽取点")

REQUIRED_FIELDS = [
    ("模块", r"\*\*模块\*\*", "缺「模块」——索引与条目无法对应"),
    ("依据", r"\*\*依据\*\*", "缺「依据」——答案无法回溯"),
    ("证据强度", r"\*\*证据强度\*\*", "缺「证据强度」——无法区分实测与推断"),
    ("一句话", r"\*\*一句话\*\*", "缺「一句话」——口述稿没有开场结论"),
    ("展开", r"\*\*展开\*\*", "缺「展开」——口述稿没有主体"),
]
EVIDENCE_WORDS = ("实测", "读码", "推断", "未核")
IGNORE_MARK = "check-faq: ignore-next-line"


def read_lines(path: Path):
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    return text.splitlines()


def blank_comments_and_fences(lines):
    """把 HTML 注释与代码围栏整段置空，保持行号不变。"""
    out, in_comment, fence = [], False, ""
    for line in lines:
        stripped = line.strip()
        if in_comment:
            if "-->" in line:
                in_comment = False
            out.append("")
            continue
        if fence:
            if stripped.startswith(fence):
                fence = ""
            out.append("")
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fence = stripped[:3]
            out.append("")
            continue
        if stripped.startswith("<!--"):
            if "-->" not in stripped:
                in_comment = True
            out.append("")
            continue
        out.append(line)
    return out


def split_row(line):
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return cells


def main() -> int:
    parser = argparse.ArgumentParser(description="技术问答库（FAQ）机械自检")
    parser.add_argument("doc", help="目标 FAQ Markdown 文件")
    parser.add_argument("--strict", action="store_true", help="出现 WARN 也返回非零")
    args = parser.parse_args()

    path = Path(args.doc)
    if not path.is_file():
        print(f"ERROR 找不到文件：{path}")
        return 2

    raw = read_lines(path)
    lines = blank_comments_and_fences(raw)
    errors, warns = [], []

    def ignored(idx):
        return idx > 0 and IGNORE_MARK in raw[idx - 1]

    # ---------------------------------------------------------- 正文条目
    entries = []  # (行号, Q号, [内容行])
    current = None
    for idx, line in enumerate(lines):
        m = BODY_HEADING.match(line)
        if m:
            current = (idx, int(m.group(1)), [])
            entries.append(current)
            continue
        if current and ANY_HEADING.match(line):
            current = None
            continue
        if current:
            current[2].append(line)

    body_numbers = [e[1] for e in entries]

    # ---------------------------------------------------------- 索引表
    index_rows = []  # (行号, Q号或None, 原始单元格)
    index_found = False
    idx_start = next((i for i, l in enumerate(lines) if INDEX_HEADING.match(l)), None)
    if idx_start is None:
        errors.append((0, "索引表", "缺少「索引」节——无法从问题导航到条目"))
    else:
        index_found = True
        seen_table = False
        for i in range(idx_start + 1, len(lines)):
            line = lines[i]
            if not line.strip():
                if seen_table and not index_rows:
                    continue
                if seen_table:
                    break
                continue
            if ANY_HEADING.match(line):
                break
            if not line.lstrip().startswith("|"):
                if seen_table:
                    break
                continue
            cells = split_row(line)
            if not seen_table:
                seen_table = True
                if cells != INDEX_HEADER:
                    errors.append((i + 1, "索引表头",
                                   f"表头应为「{' | '.join(INDEX_HEADER)}」，实际为「{' | '.join(cells)}」"))
                continue
            if all(SEPARATOR_CELL.match(c) for c in cells if c):
                continue
            if ignored(i):
                continue
            m = ROW_NUMBER.match(cells[0]) if cells else None
            if not m:
                errors.append((i + 1, "索引行", f"首列应为 Qn，实际为「{cells[0] if cells else ''}」"))
                continue
            if len(cells) != len(INDEX_HEADER):
                warns.append((i + 1, "索引列数",
                              f"应为 {len(INDEX_HEADER)} 列，实际 {len(cells)} 列"))
            index_rows.append((i + 1, int(m.group(1)), cells))

    index_numbers = [r[1] for r in index_rows]

    # ---------------------------------------------------------- 一致性
    only_body = sorted(set(body_numbers) - set(index_numbers))
    only_index = sorted(set(index_numbers) - set(body_numbers))
    for n in only_body:
        errors.append((0, "索引缺失", f"正文有 Q{n}，索引表里没有对应行"))
    for n in only_index:
        errors.append((0, "正文缺失", f"索引表有 Q{n}，正文里没有对应条目"))

    for label, numbers in (("正文", body_numbers), ("索引", index_numbers)):
        seen = set()
        prev = 0
        for n in numbers:
            if n in seen:
                errors.append((0, "Q号重复", f"{label}中 Q{n} 出现了不止一次"))
            elif n < prev:
                errors.append((0, "Q号乱序", f"{label}中 Q{n} 出现在 Q{prev} 之后"))
            seen.add(n)
            prev = max(prev, n)

    # 索引里完全相同的问法
    question_cells = {}
    for lineno, n, cells in index_rows:
        if len(cells) >= 2:
            key = re.sub(r"[\s，。？！?!,.、：:；;]", "", cells[1])
            if key:
                if key in question_cells:
                    errors.append((lineno, "重复问题",
                                   f"与 Q{question_cells[key]} 的问法完全相同，应原地更新"))
                else:
                    question_cells[key] = n

    # ---------------------------------------------------------- 条目字段
    for lineno, n, content in entries:
        block = "\n".join(content)
        for name, pattern, msg in REQUIRED_FIELDS:
            if not re.search(pattern, block):
                errors.append((lineno + 1, f"Q{n} 缺字段", msg))

        ev = re.search(r"\*\*证据强度\*\*\s*[：:]\s*(.+)", block)
        if ev and not any(w in ev.group(1) for w in EVIDENCE_WORDS):
            errors.append((lineno + 1, f"Q{n} 证据强度",
                           "证据强度须落在 实测 / 读码 / 推断 / 未核 四档之内"))

        if "**可能被追问**" not in block:
            warns.append((lineno + 1, f"Q{n} 缺追问",
                          "建议补 1–3 条「可能被追问」——这是面试价值最高的一段"))

        one = re.search(r"\*\*一句话\*\*\s*[：:]\s*(.*)", block)
        if one and not one.group(1).strip():
            warns.append((lineno + 1, f"Q{n} 一句话为空",
                          "一句话应当就是口述稿的开场结论"))

    # 行号锚点
    if any(LINE_NUMBER_IN_ANCHOR.search(l) for l in lines) and not any(
        DRIFT_DECLARED.search(l) for l in lines
    ):
        for i, l in enumerate(lines):
            if LINE_NUMBER_IN_ANCHOR.search(l):
                warns.append((i + 1, "锚点行号",
                              "依据里带了行号，但全文未声明行号会漂"))
                break

    # 过度自信提示
    if entries and not any("未核" in l for l in lines):
        warns.append((0, "证据强度",
                      "全库没有一处「未核」——确认是不是把没验过的地方写实了"))

    # ---------------------------------------------------------- 输出
    for lineno, rule, msg in errors:
        loc = f"第 {lineno} 行" if lineno else "全文"
        print(f"ERROR [{rule}] {loc}：{msg}")
    for lineno, rule, msg in warns:
        loc = f"第 {lineno} 行" if lineno else "全文"
        print(f"WARN  [{rule}] {loc}：{msg}")

    print("-" * 60)
    print(f"检查完成：ERROR {len(errors)} 项，WARN {len(warns)} 项 · {path}")
    print("提示：机械项通过 ≠ 答案合格。念一遍「一句话 + 展开」，按 references/作答体例.md 的念稿自检再过一遍。")
    if errors:
        return 1
    if warns and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
