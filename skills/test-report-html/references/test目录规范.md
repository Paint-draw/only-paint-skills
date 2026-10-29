# test/ 目录规范

测试脚本散在各处，最后一定变成「不知道哪份是最新的」。统一放 `test/`，四类东西各归各位：

```
test/
├── README.md        怎么跑、怎么出报告
├── scripts/         冒烟矩阵、端到端脚本
├── results/         运行结果 JSON（脚本产物）
├── evidence.json    汇总读数（collect_evidence.py 生成）
└── report.json      报告叙事（人写）
```

`test/` 要进版本管理。框架自己生成的报告（`target/surefire-reports`、`build/test-results`）不进——它们是产物；但 `test/results/` 里的结果要进，因为报告的数字靠它追溯。

## scripts/

- 只读的冒烟、端到端、验收脚本放这里，一个脚本一件事。
- 账号口令走环境变量（`TEST_PASSWORD`、`TEST_BASE_URL`），不要写死；演示环境的默认值可以写在 README 里。
- 脚本必须把结果写进 `test/results/<脚本名>.json`，形状见下。
- 一次性探针（临时查接口、导数据）不进这里，用完即删——留在 `scripts/` 会被当成可复用件被人照抄。

## results/

每条结果两个必备字段：

```json
{"flow": "09 档案对话 + 批量通知", "status": "PASS", "detail": "命中 27 家", "seconds": 15.7}
```

- `flow` 写人话，会直接印在报告里；
- `status` 只用 `PASS` / `FAIL` / `SKIP`；
- `detail` 写可核对的事实（条数、公司名、状态流转），不写「正常」「OK」这种没有信息量的词。

失败不要 try/except 吞掉。吞掉的那条在报告里会变成「全部通过」的一部分，而这个谎很难事后发现。

冒烟矩阵的产物要带 `"kind": "matrix"`（端到端脚本默认按 `e2e` 算）。两类分开计数：矩阵是「端点 × 角色」的调用次数，端到端是业务闭环条数，混在一个数字里会得出「本季度 179 条业务闭环」这种没法解释的读数。

## evidence.json

由 `collect_evidence.py` 生成，不要手改。结构：

```json
{
  "generated_at": "2026-10-29T17:40:00+08:00",
  "project": "/abs/path",
  "total": {"tests": 363, "failures": 0, "errors": 0, "skipped": 0, "files": 46},
  "modules": [{"name": "sai-bootstrap", "tests": 116, "classes": 23, "...": "..."}],
  "runs_total": {"count": 33, "failed": 0, "files": 3},
  "matrix_total": {"calls": 146, "problems": 0, "files": 3},
  "test_reports": {"files": [{"path": "...", "framework": "maven-surefire", "tests": 5, "mtime": "..."}]},
  "runs": [{"name": "e2e_full", "count": 22, "failed": 0, "items": ["..."]}],
  "warnings": ["..."]
}
```

改测试、改代码之后先重跑它，再出报告；跳过这一步，报告就是旧读数配新叙事。

## report.json

叙事部分，结构：

```json
{
  "eyebrow": "内测上线前 · 全功能回归",
  "title": ["平台名称", "功能需求清单与测试报告"],
  "summary": "一两句话说明覆盖范围",
  "meta": ["测试日期：...", "环境：...", "结论：..."],
  "cards": [{"value": "{{tests.total}}", "label": "后端自动化用例", "style": "accent"}],
  "sections": [
    {"no": "01", "title": "...", "lead": "...", "layout": "two",
     "columns": [[{"type": "table", "headers": [], "rows": [[]]}], [{"type": "bullets", "items": []}]]},
    {"no": "02", "title": "...", "blocks": [{"type": "table", "title": "...", "headers": [], "rows": [[]]}]}
  ],
  "footer": "..."
}
```

可用块类型：

| type | 字段 | 说明 |
|---|---|---|
| `paragraph` | `text` | 一段话 |
| `bullets` | `items`、可选 `title` | 无序列表 |
| `table` | `headers`、`rows`、可选 `title` | 单元格可内嵌 HTML（`<span class="tag ok">通过</span>`） |
| `note` | `text` | 虚线提示框 |
| `evidence` | — | 由脚本自动附在文末，不用手写 |

第一节用 `columns: [[块...],[块...]]` 出两栏，其余节用 `blocks`。

卡片 `value` 规则：

- 优先用占位符：`{{tests.total}}`、`{{tests.classes}}`、`{{runs.count}}`、`{{matrix.calls}}`、`{{modules.<模块名>.tests}}`；
- 确实要手写的数字必须带 `"source": "出处"`，否则 `build_report.py` 直接报错停下。

这是唯一能挡住「数字手抄漂移」的闸门——上一版报告里 69 个用例挂了三个月，就是因为它是一个手写的数字。
