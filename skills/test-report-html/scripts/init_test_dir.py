#!/usr/bin/env python3
"""在目标项目铺一个 test/ 目录：脚本、结果、证据、报告叙事各归各位。

用法：
    python init_test_dir.py --project /path/to/project
    python init_test_dir.py --project . --force     # 覆盖模板脚本

已存在的文件默认不覆盖——这些脚本会被改成本项目的东西，覆盖等于删工作。
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

README = """# test/

本目录集中放测试脚本与它们的产物，报告从这里生成。

```
test/
├── scripts/       冒烟矩阵、端到端脚本（Python）
├── results/       每次运行写出的 JSON 结果（脚本产物，可提交）
├── evidence.json  各测试报告的汇总读数（collect_evidence.py 生成）
└── report.json    报告叙事（人写；数字用 {{占位符}} 引用 evidence）
```

## 怎么跑

```bash
# 1. 只读接口 × 角色冒烟（先改 scripts/smoke_matrix.py 里的 ROLES / PATHS）
TEST_BASE_URL=http://localhost:8080 TEST_PASSWORD='...' python scripts/smoke_matrix.py

# 2. 端到端闭环（照 scripts/harness.py 的用法写自己的 e2e 脚本）
TEST_BASE_URL=http://localhost:8080 python scripts/e2e_full.py

# 3. 汇总证据 → 生成报告
python <skill>/scripts/collect_evidence.py --project .
python <skill>/scripts/build_report.py --project . --out docs/internal-test-report.html
```

## 约定

- 账号口令走环境变量（`TEST_PASSWORD` / `TEST_BASE_URL`），不要写死在脚本里。
- 结果文件必须是 `[{"flow": "...", "status": "PASS|FAIL", "detail": "..."}]` 形状，
  报告里的「端到端 N 条」就数它。
- 失败不要 try/except 吞掉；吞掉的那条在报告里就是一句假话。
- 覆盖统计（可选）写 `results/negative_coverage.json`：`kind` 固定 `"coverage"`，
  带上 `negative`（负向用例数）、`boundary`、`method` 与 `method_note`。口径见
  `references/test目录规范.md`。没有这份文件时，报告里覆盖质量那几格显示「未统计」。
"""

EVIDENCE_STUB = """{
  "generated_at": null,
  "project": ".",
  "total": {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "files": 0},
  "modules": [],
  "runs_total": {"count": 0, "failed": 0, "files": 0},
  "test_reports": {"files": []},
  "runs": [],
  "warnings": ["尚未运行 collect_evidence.py"]
}
"""

REPORT_STUB = """{
  "eyebrow": "内测上线前 · 全功能回归",
  "title": ["项目名称", "功能需求清单与测试报告"],
  "summary": "覆盖哪些端、验证了哪些维度，一两句话。",
  "meta": [
    "测试日期：这里写现读的日期",
    "环境：这里写现读的版本号（数据库迁移号等）",
    "结论：通过 / 有条件通过"
  ],
  "cards": [
    {"value": "{{tests.total}}", "label": "后端自动化用例全部通过", "style": "accent"},
    {"value": "{{runs.count}}", "label": "端到端业务闭环"},
    {"value": "{{tests.failures}}", "label": "失败用例", "style": "pass"}
  ],
  "sections": [
    {
      "no": "01", "title": "测试范围与方法",
      "lead": "从接口、页面、业务闭环三个层次验证。",
      "blocks": [
        {"type": "table", "title": "自动化用例分账",
         "headers": ["模块", "用例", "失败"],
         "rows": [["模块名", "{{modules.模块名.tests}}", "{{tests.failures}}"]]}
      ]
    }
  ],
  "footer": "项目名称 · 测试报告"
}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--force", action="store_true", help="覆盖已存在的模板脚本")
    args = ap.parse_args()

    root = Path(args.project).resolve()
    test = root / "test"
    for sub in ("scripts", "results"):
        (test / sub).mkdir(parents=True, exist_ok=True)

    created = []
    for asset in ("harness.py", "smoke_matrix.py"):
        dst = test / "scripts" / asset
        if dst.exists() and not args.force:
            continue
        shutil.copyfile(ASSETS / asset, dst)
        created.append(dst.relative_to(root).as_posix())

    for name, body in (("README.md", README), ("evidence.json", EVIDENCE_STUB), ("report.json", REPORT_STUB)):
        dst = test / name
        if dst.exists():
            continue
        dst.write_text(body, encoding="utf-8")
        created.append(dst.relative_to(root).as_posix())

    if created:
        print("已创建：")
        for c in created:
            print("  " + c)
    else:
        print("test/ 已就绪，无需创建。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
