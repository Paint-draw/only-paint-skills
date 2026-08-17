# 场景 2：功能开发（最常用的日常流程）

**触发信号**：已有 `master` + `dev`，用户要开发新功能 / 改代码 / 修非线上 bug。

## 分支命名规范

| 类型 | 格式 | 示例 |
|---|---|---|
| 单人功能 | `feature/功能-日期` | `feature/login-0814` |
| 多人功能 | `feature/功能-日期-姓名` | `feature/login-0814-zhangsan` |

日期用 `MMDD` 格式。

## 步骤

```bash
# 1. 确保 dev 最新，再从 dev 拉出 feature 分支
git checkout dev
git pull origin dev
git checkout -b feature/功能-日期

# 2. 在 feature 上开发，小步多次提交（commit message 见 commit-convention.md）
git add .
git commit -m "feat(登录): 新增手机验证码登录"

# 3. 开发完成，把最新 dev 合并进 feature（先在本地解决冲突）
git checkout dev && git pull origin dev
git checkout feature/功能-日期
git merge dev              # 有冲突在此解决，解决后编译/运行验证

# 4. 推送 feature 到远程（用于备份 / 给同事看 / 发起 MR）
git push origin feature/功能-日期

# 5. 合并回 dev（禁止直接 push dev，推荐走 Merge Request；合并用 --no-ff）
git checkout dev
git merge --no-ff feature/功能-日期 -m "feat: 合并登录功能"
git push origin dev

# 6. 删除 feature 分支（本地 + 远程）
git branch -d feature/功能-日期
git push origin --delete feature/功能-日期
```

## 何时开分支 / 何时不开

| 情形 | 是否开分支 |
|---|---|
| 开发新功能 / 需求 | ✅ 开 `feature/*` |
| 一个功能多人并行 | ✅ 每人一条 `feature/功能-日期-姓名` |
| 改一行注释 / 文档小改动 | ❌ 通常不必，直接在 dev 小步提交（团队约定） |
| 修别人正在开发的同一功能的 bug | ❌ 别开新分支，在同一条 feature 上协作 |

**判断口诀**：改动会影响主线稳定性，或需要独立发布 / 独立评审，就开分支；纯粹琐碎、当天能完成且不干扰他人的小改动，才考虑直接在 dev 提交。

## 何时推送

- 需要备份 / 换机器 / 给同事看 / 请人 review / 提测时 → push 自己的 `feature/*`。
- 每天下班前 push，代码不留在本地。
- **不要每写完一行就推**，小步本地 commit，阶段性 push。

## 何时合并回 dev

- 功能开发完成 + 自测通过 + 评审通过后，才把 feature 合并回 dev。
