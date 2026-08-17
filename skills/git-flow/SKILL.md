---
name: git-flow
description: >-
  团队 Git 开发流程规范（基于 Git Flow）。当用户做任何 Git/版本管理相关动作时使用本 skill——
  初始化仓库、创建/切换/删除分支、开发新功能、提交代码、合并、推送、拉取、打 tag、解决冲突、
  提测、发布版本、紧急修复线上 bug，或询问「什么时候开分支/推送/合并」「分支怎么命名」「commit 规范」等问题。
  加载后必须先探测当前仓库状态，再路由到 初始化/功能开发/提测发布/线上修复 四个场景，
  输出可执行命令并强制红线。即使用户没有明确说「git」或「分支」，只要是在做版本管理动作就应使用本 skill。
---

# Git Flow 开发流程规范

本 skill 把团队的 Git Flow 规范从「文档」变成「可执行动作」：先探测仓库状态，再路由到正确场景，输出该场景的完整命令序列，并强制红线。

## 核心原则

- `master`（或 `main`）任何时候都是稳定可发布版本，**任何人禁止直接 push**，只能通过合并进入。
- `dev` 是日常开发集成线，存放最新开发版本，一般也不直接提交。
- `feature` / `release` / `hotfix` / `issue` 是短期分支，**用后即删**。
- 每次提交、每条分支都要有明确的去向。

## 第一步：探测仓库状态（决定路由）

按顺序探测，判断项目处于哪个阶段。用 Bash 工具执行只读命令，不要盲目假设：

1. `git rev-parse --is-inside-work-tree` → 不在 git 仓库（报错）说明要**初始化**（场景 1）。
2. `git branch -a` → 看有没有 `master`/`main` 和 `dev`。
3. `git tag` → 看有没有已发布版本（有 tag 说明已上线）。
4. `git branch --show-current` → 当前在哪个分支。
5. `git remote -v` → 有没有远程仓库。
6. `git status --short` → 工作区是否有未提交改动（合并/切分支前必须检查）。

### 路由表

| 探测到的信号 | 场景 | 读哪个 reference |
|---|---|---|
| 无 `.git` / 空仓库 | 场景 1：初始化 | `references/scenario-init.md` |
| 已有 master+dev，用户要开发新功能/改代码 | 场景 2：功能开发 | `references/scenario-feature.md` |
| 功能合完，用户要提测/发布版本 | 场景 3：提测发布 | `references/scenario-release.md` |
| 已上线（有 tag），线上出 bug 要紧急修复 | 场景 4：线上修复 | `references/scenario-hotfix.md` |
| 用户只是要提交/合并/推送/写 commit | 通用动作 | 见下方红线 + `references/commit-convention.md` |

判断不明确时，用一句话向用户确认所处阶段，再执行——不要猜错场景。

## 红线（任何场景都强制，不可跳过）

1. **push 前必须 pull**：顺序固定 `pull → 解决冲突 → 编译/运行验证 → push`，防止覆盖他人代码。
2. **禁止 `git push -f`** 强推，禁止向远端 `git reset --hard`，禁止删除他人分支。
3. **`master` 上的 tag 一旦推送，不可移动或删除**——发布版本不可变。
4. **合并一律用 `git merge --no-ff`**，保留分支合并痕迹，方便追溯。
5. **一个 commit 只做一件事**，不要「修 bug 顺带改了一堆无关功能」。
6. **`release` 和 `hotfix` 必须同时合并回 `master` 和 `dev`**，否则会出现「线上修好了、开发线还在报错」的分叉。
7. 合并/切分支前先 `git status` 确认工作区干净，避免把未完成改动带走。

## 第二步：按场景输出可执行命令

根据路由结果，读取对应 reference 文件，把命令里的 `<占位符>` 替换成真实的仓库地址、分支名、版本号、commit message 后输出给用户。不要只复述规范，要给出「可直接复制执行」的命令序列。

## 提交规范

任何涉及 `git commit` 的动作，先读 `references/commit-convention.md`，按 `type(scope): subject` 格式写 commit message。

## 常用命令速查

| 功能 | 命令 |
|---|---|
| 创建并切换分支 | `git checkout -b <分支名>` |
| 查看分支 | `git branch -a` |
| 删除本地分支 | `git branch -d <分支名>` |
| 删除远程分支 | `git push origin --delete <分支名>` |
| 合并（禁 fast-forward） | `git merge --no-ff <分支> -m "说明"` |
| 打标签 | `git tag -a v1.2.0 -m "说明"` |
| 查看提交图 | `git log --oneline --graph` |
