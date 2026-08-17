# only-paint-skills

个人开发的 Claude Code skill 集合，作为一个 plugin 统一管理、整体分发（方案 B：一个 plugin 装多个 skill，整体一个版本号）。

## 包含的 skill

| skill | 说明 |
|---|---|
| `git-flow` | 团队 Git Flow 开发流程规范 |
| `skill-release-manager` | skill/plugin 版本管理与发布工具 |
| `business-logic:init` | 建立并维护「业务逻辑白皮书」（建档 / 查漏补缺） |
| `business-logic:improve` | 完善/优化业务逻辑（三顶帽子 + 对抗式审查门 + 实施计划） |
| `business-logic:execute` | 照实施计划落地代码 + 同步白皮书 |

## 目录结构

```
only-paint-skills/
├── .claude-plugin/
│   ├── plugin.json          ← 唯一 version，管下面所有 skill
│   └── marketplace.json     ← 对外分发索引
├── skills/
│   ├── git-flow/
│   ├── skill-release-manager/
│   ├── business-logic-init/
│   ├── business-logic-improve/
│   └── business-logic-execute/
├── CHANGELOG.md
└── README.md
```

## 两种使用方式

### 开发态（自己用，改了立即生效）

把 `skills/` 下的 skill 软链接到 `~/.claude/skills/`，Claude 直接读真身，改动即时生效，无需重装：

```
~/.claude/skills/git-flow              → <本仓库>/skills/git-flow
~/.claude/skills/skill-release-manager → <本仓库>/skills/skill-release-manager
~/.claude/skills/business-logic-init      → <本仓库>/skills/business-logic-init
~/.claude/skills/business-logic-improve   → <本仓库>/skills/business-logic-improve
~/.claude/skills/business-logic-execute   → <本仓库>/skills/business-logic-execute
```

> Windows 下建 symlink 请用 PowerShell 的 `New-Item -ItemType SymbolicLink`，git bash 的 `ln -s` 会回退成复制。

### 分发态（给别人用，版本化快照）

把本仓库 push 到 GitHub 后，别人通过 marketplace 安装：

```
/plugin marketplace add <你的GitHub用户名>/only-paint-skills
/plugin install only-paint-skills
```

装上后 skill 会带前缀：`only-paint-skills:git-flow`、`only-paint-skills:skill-release-manager`。

## 发版

改动任一 skill 后，触发 `skill-release-manager` 走发布流程（升版本号 → 同步 plugin.json/marketplace.json → 更新 CHANGELOG → commit + tag + push）。
