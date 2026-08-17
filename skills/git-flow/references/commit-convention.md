# 提交信息规范（Commit Message）

格式统一为：`<type>(<scope>): <subject>`

## type 类型

| type | 含义 |
|---|---|
| `feat` | 新增功能 |
| `fix` | 修复 bug |
| `docs` | 仅改文档 |
| `style` | 仅改空格 / 格式 / 缩进，不改逻辑 |
| `refactor` | 重构，无新功能无 bug 修复 |
| `perf` | 性能优化 |
| `test` | 增加 / 修改测试 |
| `chore` | 构建流程、依赖、工具变动 |
| `revert` | 回滚到上一版本 |
| `init` | 初始化 |
| `build` | 构建相关 |

`scope` 是影响范围，如 `auth`、`order`、`pay`、`route`、`utils` 等，可省略。
`subject` 是一句话概述，用中文或英文保持一致即可。

## 示例

```
feat(auth): 新增手机验证码登录
fix(pay): 修复支付回调验签失败
docs(readme): 补充部署说明
refactor(order): 抽离订单状态机
chore(deps): 升级 prisma 到 5.x
```

## 作者配置（一次性）

```bash
git config --global user.name "张三"
git config --global user.email "zhangsan@example.com"
```
