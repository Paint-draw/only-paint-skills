# Changelog

所有值得注意的变更都会记录在这个文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [Semver](https://semver.org/lang/zh-CN/)。

## [1.2.1] - 2026-08-19

### Changed
- 【business-logic-init / business-logic-improve / business-logic-execute】skill `name` 与全部交叉引用统一为连字符形式，符合技能命名规范（仅字母/数字/连字符）

## [1.2.0] - 2026-08-19

### Changed
- 【git-flow】新增红线 8：提交/推送前按需同步 README.md，确保 README 描述当前最新实现（新增 `references/readme-sync.md` 判断流程）

## [1.1.0] - 2026-08-17

### Added
- 【business-logic-init】新增「业务逻辑白皮书」建档/查漏 skill（由原 business-logic-workflow 拆分）
- 【business-logic-improve】新增业务逻辑完善/优化 skill（三顶帽子 + 对抗式审查门 + 实施计划）
- 【business-logic-execute】新增实施计划落地代码 skill（分步执行 + 验证分层 + 白皮书同步）

## [1.0.0] - 2026-08-17

### Added
- 【git-flow】团队 Git Flow 开发流程规范（初始化 / 功能开发 / 提测发布 / 线上修复四场景）
- 【skill-release-manager】skill/plugin 版本管理与发布工具（方案 B：一个 plugin 整体发版）
