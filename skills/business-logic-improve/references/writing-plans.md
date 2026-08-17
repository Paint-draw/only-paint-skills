# writing-plans（内联版）—— 写实施计划草稿的方法

> 本文件是 `superpowers:writing-plans` 技能的完整内容内联。模式② 打计划草稿时照此执行，不再依赖外部技能。

## 概述

写详尽的实施计划，假设执行者对这个代码库零上下文、品味存疑。文档化他需要知道的一切：每个任务要动哪些文件、代码、测试、可能要查的文档、怎么测。把整个计划拆成一口大小的任务。DRY。YAGNI。TDD。频繁提交。

假设执行者是熟练开发者，但对工具链和问题域几乎一无所知。假设他不太懂好的测试设计。

**开始前宣布：** "我正在用 writing-plans 方法写实施计划。"

## 范围检查

如果 spec 覆盖多个独立子系统，brainstorming 阶段就该拆成子项目 spec。没拆就建议拆成多个独立计划——每个子系统一份，每份都能独立产出可用、可测的软件。

## 文件结构

定义任务前，先规划哪些文件会被创建或修改、各自负责什么。这是分解决策落定的地方。

- 设计边界清晰、接口明确的最小单元。每个文件一个明确职责。
- 你只能同时 hold 住有限上下文来推理代码，文件聚焦时编辑更可靠。偏好更小、更聚焦的文件，而不是做太多事的大文件。
- 一起变的文件放一起。按职责拆，不按技术层拆。
- 已有代码库遵循既有模式。代码库用大文件就别单方面重构——但如果你正在改的文件变得臃肿，在计划里合理拆分也可以。

这个结构决定任务分解。每个任务产出自洽、能独立成立的改动。

## 一口大小的任务粒度

**每步是一个动作（2-5 分钟）：**
- "写失败测试" - step
- "跑确认它失败" - step
- "写最小实现让它过" - step
- "跑测试确认过" - step
- "提交" - step

## 计划文档头

**每份计划必须以这个 header 开头：**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** Steps use checkbox (`- [ ]`) syntax for tracking. 执行阶段用 `business-logic:execute` 落地。

**Goal:** [一句话描述要构建什么]

**Architecture:** [2-3 句描述方案]

**Tech Stack:** [关键技术/库]

---
```

## 任务结构

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## 没有占位符

每一步必须包含执行者实际需要的内容。这些是**计划失败**——永远不要写：
- "TBD"、"TODO"、"以后实现"、"填细节"
- "加合适的错误处理" / "加校验" / "处理边界情况"
- "给上面的写测试"（没有实际测试代码）
- "同 Task N"（重复代码——执行者可能乱序读任务）
- 只描述做什么而不展示怎么做的步骤（代码步骤必须给代码块）
- 引用任何任务中都没定义的类型、函数、方法

## 记住
- 永远精确文件路径
- 每步完整代码——改代码的步骤就展示代码
- 精确命令 + 预期输出
- DRY、YAGNI、TDD、频繁提交

## 自审

写完完整计划后，用 fresh eyes 对照 spec 检查。这是你自己跑的 checklist——不是派子智能体。

**1. Spec 覆盖：** 扫一遍 spec 每个章节/需求。能指到一个实现它的任务吗？列出缺口。

**2. 占位符扫描：** 搜计划里「没有占位符」一节的红旗模式，修掉。

**3. 类型一致性：** 后面任务用的类型、方法签名、属性名和前面任务定义的一致吗？Task 3 叫 `clearLayers()` 但 Task 7 叫 `clearFullLayers()` 是 bug。

发现问题就地修，不用重新审——修完继续。spec 需求没有对应任务就加任务。

## 执行交接

存完计划后提供执行选择——模式② 的最终去向是 `business-logic:execute`。
