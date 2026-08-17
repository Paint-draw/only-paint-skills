# 场景 3：测试、缺陷修复与版本发布

**触发信号**：功能已合回 dev，用户要提测 / 发布新版本。

## 版本号规范

格式 `x.y.z`：
- `x` 主版本 —— 重大重构、不兼容变更才升级；
- `y` 次版本 —— 新增功能时升级；
- `z` 修订号 —— 修复 bug 时升级。

## 步骤

```bash
# 1. 从 dev 拉出 release 分支，提交测试
git checkout dev && git pull origin dev
git checkout -b release/1.2.0
git push origin release/1.2.0

# 2. 测试发现缺陷：从 release 拉出 issue 子分支修复
git checkout -b issue/登录-修复校验
# ...修复、提交...
git checkout release/1.2.0
git merge --no-ff issue/登录-修复校验
git branch -d issue/登录-修复校验        # 修复完即删

#    （重复步骤 2，直到测试全部通过）

# 3. 测试通过，合并到 master 并打 tag 发布
git checkout master
git merge --no-ff release/1.2.0 -m "release: 发布 v1.2.0"
git tag -a v1.2.0 -m "v1.2.0 正式版"
git push origin master --tags

# 4. 同步回 dev（把测试期修复带回开发线，防止 dev 丢修复）
git checkout dev
git merge --no-ff release/1.2.0
git push origin dev

# 5. 删除 release 分支
git branch -d release/1.2.0
git push origin --delete release/1.2.0
```

## 要点

- `release` 合并回 `master` **和** `dev` 两步缺一不可——跳过回 dev 会让开发线丢掉测试期修复。
- tag 打在 `master` 上，一旦推送不可移动。
- 提测阶段的 bug 用 `issue/*` 子分支从 `release/*` 拉出，修完合并回 `release/*` 即删。
