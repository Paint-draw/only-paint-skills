# 场景 1：项目初始化

**触发信号**：当前目录不在 git 仓库内（`git rev-parse --is-inside-work-tree` 报错），或是一个空仓库，用户要初始化项目。

## 步骤

```bash
# 1. 初始化仓库
git init

# 2. 先建 .gitignore，再首次提交
#    至少忽略：node_modules/、dist/、build/、.env、*.log、.DS_Store、IDE 配置等
git add .
git commit -m "init: 初始化项目"

# 3. 关联远程仓库（把 <仓库地址> 替换成真实地址）
git remote add origin <仓库地址>

# 4. 推送 master
git push -u origin master

# 5. 从 master 拉出 dev，作为日常开发集成线
git checkout -b dev
git push -u origin dev
```

## 要点

- `.gitignore` 必须在第一次 commit 前建好，否则构建产物、依赖目录、本地配置会被误提交进历史，之后清理很麻烦。
- 首次 commit 用 `init:` 前缀（见 `commit-convention.md`）。
- 建完后确认：远程有 `master` 和 `dev` 两个长期分支，`master` 受保护（禁止直接 push）。
