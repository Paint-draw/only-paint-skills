---
name: skill-release-manager
description: >-
  管理并发布个人 Skill / Plugin 的新版本。当用户要维护、更新、迭代、发布自己的 plugin（一个 plugin 装多个 skill）时使用——
  例如「更新我的 skill」「给这个 plugin 发个新版本」「升级版本号」「打 tag 发布」「帮我把这个 plugin 发布出去」，
  或刚改完 plugin 仓库里 skills/ 下某个 skill 的内容、要把它推进到可分发的新版本时。
  本 skill 面向「方案 B：一个 plugin 整体发版」结构——一个 plugin.json 用一个 version 管 skills/ 下所有 skill。
  它会：探测 plugin 仓库 → 分析 skills/ 下本次改动并判断 semver 递增 → 同步 plugin.json 的 version 与 marketplace.json 的 ref →
  更新 CHANGELOG（标注动了哪个 skill）→ git commit + tag + push → 跑检查清单，拦截「两个 JSON 不同 commit」「tag 与 version 不一致」等易错点。
  即使用户没明说「发布」，只要在维护一个 plugin 仓库并改了 skill，就应考虑使用本 skill。
---

# Skill / Plugin 版本管理与发布（方案 B：一个 plugin 整体发版）

把一个「已经改完内容的 plugin 仓库」推进到「可分发的新版本」：自动定版本号、同步三个文件、走完 git 流程、兜底易错点。

## 这套结构长什么样

本 skill 假设你的仓库是「一个 plugin 装多个 skill」：

```
<plugin仓库>/
├── .claude-plugin/
│   ├── plugin.json          ← 唯一 version，管下面所有 skill
│   └── marketplace.json     ← 对外分发索引
├── skills/                  ← 你的所有 skill 都在这
│   ├── skill-a/SKILL.md
│   └── skill-b/SKILL.md
├── CHANGELOG.md
└── README.md
```

**发版粒度 = 整个 plugin**：改 `skills/` 下任何一个 skill，都是给整个 plugin 升一次版本。

## 核心原则

- **一个 plugin 一个 version**：`plugin.json` 的 `version` 是唯一权威，`git tag` 和 `marketplace.json` 的 `ref` 都必须对齐它。
- **一次发布 = 一个 commit**：`plugin.json`、`marketplace.json`、`CHANGELOG.md` 三个文件同一个 commit，这是最高频事故点。
- **tag 名带 `v` 前缀**：version `1.2.0` → tag `v1.2.0`，marketplace 的 `ref` 也写 `v1.2.0`。
- **push 前必须让用户确认一次**，push + `push --tags` 是唯一不可逆动作。

## 第一步：定位 plugin 仓库

按顺序确定仓库根目录（标准 = 有 `.claude-plugin/plugin.json`）：

1. 用户给了路径 → 用该路径。
2. 用户说了 plugin/skill 名 → 先到 `~/.claude/skills/` 下找（注意那里可能是 symlink，用 `readlink` 解析到真身仓库）。
3. 都没给 → 从当前目录逐级向上找 `.claude-plugin/plugin.json`。

找到后确认 `plugin.json` 的 `skills` 数组列出了 `skills/` 下的所有 skill。

## 第二步：分析本次改动

用只读命令搞清楚「这次改了 skills/ 下哪些 skill」：

```bash
git -C <仓库> status --short
git -C <仓库> diff --stat
git -C <仓库> log --oneline -5
```

把改动归类（**因为是整体发版，取所有改动里最严重的那档**）：

| 改动类型 | 例子 | 版本号 |
|---|---|---|
| 修 bug、改错别字、优化描述 | 修复崩溃、改 typo | PATCH (+0.0.1) |
| 新增功能、新增触发场景、向后兼容 | 加触发场景、支持新文件 | MINOR (+0.1.0) |
| 破坏性变更、旧用法不兼容 | 重写核心逻辑、改参数结构 | MAJOR (+1.0.0) |

**判断完先展示给用户确认**，输出形如：

```
检测到改动：skills/git-flow 新增了 X 场景；skills/skill-release-manager 修了 Y 崩溃
建议版本：1.0.0 → 1.1.0（MINOR，新增功能为主，无破坏性）
动了：git-flow、skill-release-manager
确认用 1.1.0 吗？还是改成 MAJOR/PATCH？
```

用户确认后记下新版本号 `N`。

## 第三步：读取并修改三个文件

先读再改：

1. `.claude-plugin/plugin.json` → `version` 改成 `N`。
2. `.claude-plugin/marketplace.json` → 对应 plugin 条目的 `source.ref` 改成 `vN`。
3. `CHANGELOG.md` → 顶部按 Keep a Changelog 加一条，**务必标注这次动了哪个 skill**：

```markdown
## [1.1.0] - YYYY-MM-DD

### Added
- 【git-flow】新增「XXX」触发场景
- 【skill-release-manager】支持 XXX

### Fixed
- 【skill-release-manager】修复 XXX 崩溃
```

没发生的分类删掉，日期用当天。

### 关于 source.sha（关键，别踩坑）

- `ref` 指向 tag 名（`vN`）—— 常规发布**只改 ref**，tag 名在打 tag 前就能确定。
- `sha` 指向具体 commit —— 只有「锁定版本」才用，且只能 `git push` 之后拿到真实 SHA 再回填。

顺序：改 `ref` → commit → tag → push →（可选）回填 `sha` 补一个 commit。**绝不要在第一次 commit 前就把 sha 写进 marketplace.json**，那时 SHA 还不存在。

## 第四步：git 提交 + 打 tag

```bash
git add .
git commit -m "release: v1.1.0 - <一句话说明>"

git tag v1.1.0
```

自查：三个文件同一个 commit、tag 与 version 一致。

## 第五步：push（先确认，唯一不可逆点）

**停下展示命令等用户确认**：

```bash
git push
git push --tags
```

## 第六步：检查清单

- [ ] plugin.json 的 version 已更新为 N
- [ ] marketplace.json 的 source.ref 已同步为 vN
- [ ] CHANGELOG.md 已加 [N] 条目、标注了动了哪个 skill
- [ ] 三个文件同一个 commit
- [ ] git tag vN 与 version 一致（含 v 前缀）
- [ ] git push + push --tags 成功

## 红线（不可跳过）

1. **三个文件同 commit**：只改 plugin.json 不改 marketplace.json，用户 update 永远看不到新版本。
2. **tag = version**：`git tag v1.2.0` 的 `v1.2.0` 必须和 `"version": "1.2.0"` 严格一致。
3. **ref 指向 tag 名，不是 sha**：常规发布只改 ref，sha 是 push 后的可选锁定。
4. **push 前必须用户确认**。
5. **不 `push -f`、不动已推送的 tag**：已发布版本不可变。

## 常见症状速查

| 症状 | 原因 | 解决 |
|---|---|---|
| 用户 update 看不到新版本 | 只改了 plugin.json 没改 marketplace.json | 同 commit 重发 |
| 安装后还是旧版 | installed_plugins.json 缓存未刷新 | 提示重装或删缓存目录 |
| git push 报 tag 冲突 | tag 已存在或与 version 不一致 | 核对 git tag，必要时删本地错误 tag 重打（未 push 前） |

---

## 附录 A：首次初始化（还没有 .claude-plugin/plugin.json）

当要新建这套「一个 plugin 装多个 skill」结构时，按下面骨架搭：

```
<plugin名>/
├── .claude-plugin/plugin.json      ← version 1.0.0
├── .claude-plugin/marketplace.json ← ref v1.0.0
├── skills/<skill-a>/SKILL.md
├── skills/<skill-b>/SKILL.md
├── CHANGELOG.md
└── README.md
```

plugin.json 骨架：

```json
{
  "name": "<plugin名>",
  "description": "<一句话>",
  "version": "1.0.0",
  "author": { "name": "<你>", "email": "<email>" },
  "license": "MIT",
  "skills": ["./skills/<skill-a>", "./skills/<skill-b>"]
}
```

搭完按第二步~第六步发 v1.0.0。
