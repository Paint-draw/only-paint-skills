# grill-with-docs（内联版）—— 与用户质询确认需求

> 本文件是原 `grill-with-docs` 技能的完整内容内联。模式② 第一步「确认需求」直接照此执行，不再依赖外部技能。

## 核心指令

对用户的这个业务改动，**逐条质询**，直到双方达成一致理解。沿着设计树的每个分支往下走，逐个解决决策点之间的依赖关系。**每个问题都要给出你的推荐答案。**

**一次只问一个问题**，等用户对每个问题给出反馈后再继续下一个。

如果一个问题能通过探索代码库回答，就先探索代码库，而不是问用户。

## 领域感知

探索代码库时，同时留意现有文档：

### 文件结构

大多数仓库是单一 context：

```
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

如果根目录存在 `CONTEXT-MAP.md`，说明仓库有多个 context。地图指向每个 context 所在位置：

```
/
├── CONTEXT-MAP.md
├── docs/
│   └── adr/                          ← 系统级决策
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md
│   │   └── docs/adr/                 ← context 专属决策
│   └── billing/
│       ├── CONTEXT.md
│       └── docs/adr/
```

**懒创建**：只在有东西可写时才创建文件。没有 `CONTEXT.md` 就先创建（当第一个术语被确认时）；没有 `docs/adr/` 就先创建（当第一个 ADR 需要时）。

## 会话中

### 对照术语表质询

当用户使用的术语与 `CONTEXT.md` 中已有语言冲突时，立即指出："你的术语表把 'cancellation' 定义为 X，但你似乎指的是 Y —— 到底是哪个？"

### 磨尖模糊语言

当用户使用含糊或过载的术语时，提出精确的规范术语。"你说 'account' —— 指的是 Customer 还是 User？这俩是不同东西。"

### 讨论具体场景

当领域关系被讨论时，用具体场景压测它们。编造探查边界的场景，逼用户在概念边界上做精确。

### 与代码交叉验证

当用户陈述某事如何运作时，检查代码是否同意。发现矛盾就挑明："你的代码是整单取消 Orders，但你刚说支持部分取消 —— 哪个对？"

### 实时更新 CONTEXT.md

术语一确认就立刻更新 `CONTEXT.md`，不要攒批。用下面的格式（见本文件末尾「CONTEXT.md 格式」）。

`CONTEXT.md` 应**完全不含实现细节**。不要把它当 spec、草稿纸、或实现决策的仓库。它是术语表，仅此而已。

### 谨慎提供 ADR

只有以下三条**同时**成立时才提议创建 ADR：

1. **难逆转** —— 事后改变主意代价大
2. **无上下文会惊讶** —— 未来的读者会想"为什么当初这么干？"
3. **真实权衡的结果** —— 确实有替代方案，你因为特定理由选了其一

三条缺一，跳过 ADR。格式见本文件末尾「ADR 格式」。

### ADR 合格标准

- **架构形态**："我们用 monorepo。""写模型是 event-sourced，读模型投影到 Postgres。"
- **context 间的集成模式**："Ordering 和 Billing 通过领域事件通信，不是同步 HTTP。"
- **带来锁定效应的技术选择**：数据库、消息总线、认证 provider、部署目标。不是每个库——只记换掉要花一个季度的那种。
- **边界与范围决策**："客户数据归 Customer context 所有；其他 context 只用 ID 引用。" 显式的"不"和"是"同样有价值。
- **偏离显而易见路径的刻意选择**："我们不用 ORM 而用原生 SQL，因为 X。" 凡是合理读者会假设相反的，都要记。这能阻止下一个人"修好"某样本是有意为之的东西。
- **代码里看不到的约束**："因为合规要求不能用 AWS。""因为伙伴 API 合同，响应必须 <200ms。"
- **被否方案当否定理由不显而易见时**：考虑了 GraphQL 却因为微妙理由选了 REST，记下来——否则六个月后又有人提 GraphQL。

## CONTEXT.md 格式

### 结构

```md
# {Context 名称}

{一两句：这个 context 是什么、为什么存在。}

## Language

**Order**:
{一两句描述该术语}
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a customer after delivery.
_Avoid_: Bill, payment request

**Customer**:
A person or organization that places orders.
_Avoid_: Client, buyer, account
```

### 规则

- **要有主见。** 多个词表达同一概念时，挑最好的一个，其余列在 `_Avoid_` 下。
- **定义要精简。** 一两句封顶。定义它**是什么**，不是它**做什么**。
- **只收录本项目 context 专属术语。** 通用编程概念（timeout、错误类型、工具模式）即使项目大量使用也不收录。加术语前自问：这是本 context 独有的概念，还是通用编程概念？只有前者才收录。
- **自然成簇时按子标题分组。** 所有术语属同一领域时，平铺列表即可。

### 单 context 与多 context

**单 context（多数仓库）：** 仓库根目录一个 `CONTEXT.md`。

**多 context：** 根目录 `CONTEXT-MAP.md` 列出各 context、位置、关系：

```md
# Context Map

## Contexts

- [Ordering](./src/ordering/CONTEXT.md) — receives and tracks customer orders
- [Billing](./src/billing/CONTEXT.md) — generates invoices and processes payments
- [Fulfillment](./src/fulfillment/CONTEXT.md) — manages warehouse picking and shipping

## Relationships

- **Ordering → Fulfillment**: Ordering emits `OrderPlaced` events; Fulfillment consumes them to start picking
- **Fulfillment → Billing**: Fulfillment emits `ShipmentDispatched` events; Billing consumes them to generate invoices
- **Ordering ↔ Billing**: Shared types for `CustomerId` and `Money`
```

推断结构：`CONTEXT-MAP.md` 存在 → 读它找 contexts；只有根 `CONTEXT.md` → 单 context；都没有 → 首个术语确认时懒创建根 `CONTEXT.md`。多 context 时，推断当前话题属于哪个；不确定就问。

## ADR 格式

ADR 存在 `docs/adr/`，顺序编号：`0001-slug.md`、`0002-slug.md`……

`docs/adr/` 目录懒创建——只在第一个 ADR 需要时。

### 模板

```md
# {决策的短标题}

{1-3 句：context 是什么、我们决定什么、为什么。}
```

就这些。ADR 可以是一个段落。价值在记录**做了**决定、**为什么**——不是填满章节。

### 可选章节

只有真正有增益时才加，多数 ADR 不需要：

- **Status** frontmatter（`proposed | accepted | deprecated | superseded by ADR-NNNN`）——决策会被重访时有用
- **Considered Options** —— 只有被否的替代方案值得记住时
- **Consequences** —— 只有非显而易见的连锁影响需要指出时

### 编号

扫 `docs/adr/` 找最大编号 +1。
