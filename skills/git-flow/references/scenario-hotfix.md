# 场景 4：线上产品缺陷修复（Hotfix）

**触发信号**：项目已上线（`master` 上有 tag），线上出现 bug 需要紧急修复。

## 步骤

```bash
# 1. 从 master（或对应 tag）拉出 hotfix 分支
git checkout master
git checkout -b hotfix/1.1.1

# 2. 修复并测试通过
git commit -m "fix(支付): 修复线上支付回调验签失败"

# 3. 合并回 master，打 tag，紧急发布
git checkout master
git merge --no-ff hotfix/1.1.1 -m "hotfix: 发布 v1.1.1"
git tag -a v1.1.1 -m "v1.1.1 紧急修复版"
git push origin master --tags

# 4. 同步回 dev（避免 dev 上还带着这个 bug）
git checkout dev
git merge --no-ff hotfix/1.1.1
git push origin dev

# 5. 删除 hotfix 分支
git branch -d hotfix/1.1.1
git push origin --delete hotfix/1.1.1
```

## 要点

- `hotfix` 版本号在 `master` 最新 tag 基础上 `z` 位 +1（如 v1.1.0 → hotfix/1.1.1）。
- 和 `release` 一样，**必须双合并回 `master` + `dev`**。
- 这是最容易出错的环节：很多人只推了 `master` 就收工，导致 dev 分支还带着线上 bug，下次发布又把它带上去。
