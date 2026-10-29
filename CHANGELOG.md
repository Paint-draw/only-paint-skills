# Changelog

所有值得注意的变更都会记录在这个文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [Semver](https://semver.org/lang/zh-CN/)。

## [Unreleased]

## [1.6.0] - 2026-10-29

### Added
- 【test-report-html】新增「测试报告生成」skill：把项目的测试证据整理成单文件 HTML 内测报告。两段式——`collect_evidence.py` 扫 surefire / Gradle / pytest / JUnit 报告与 `test/results/*.json` 汇总出 `test/evidence.json`（用例数只认 `<testcase>`，避免 `@Nested` 少报造成的假绿），`build_report.py` 把 `report.json` 里的 `{{tests.total}}` 占位符换成读数并渲染；占位符解不出、卡片用无出处的手写数字时直接拒绝出报告。附 `init_test_dir.py` 铺设统一 `test/` 目录、`assets/harness.py` 端到端骨架、`assets/smoke_matrix.py` 角色 × 接口冒烟骨架，以及报告体例 / 证据来源 / test 目录规范三份 references
- 【plugin】`plugin.json` 升 1.6.0 并登记新 skill，`marketplace.json` ref 同步 `v1.6.0`，README 补条目与软链说明

## [1.5.0] - 2026-10-24

### Added
- 【tech-to-md】新增「技术底层实现文档」写作 skill：照代码取证书写模块机制链条、层间数据形状、设计理由与取舍、被否方案与证据强度，产物遵循《技术文档体例》（六类必写 / 五类禁写 / 五要素 / 三块收尾）；附取证指南、自查清单、文档模板与 `scripts/check-doc.py` 禁写项自检，并支持文末「速答卡」与旧文档增量维护
- 【tech-faq-drill】新增「技术问答演练」skill：用户扮演面试官提问、Claude 扮演被面试者，基于 `docs/` 技术文档与代码真实实现作答；答案按「结论 → 机制 → 取舍与代价 → 边界」组织成可直接照念的口述稿，文档与代码冲突时以代码为准并在核对区说明；问答追加进 `docs/FAQ/FAQ.md` 单一问答池（Q 号全局递增、同义问题原地更新），附作答体例、定位核对指南、FAQ 体例、模板与 `scripts/check-faq.py` 索引一致性自检
- 【plugin】`plugin.json` / `marketplace.json` / `README.md` 登记两个新 skill，marketplace 描述补齐技术类 skill

## [1.4.0] - 2026-09-21

### Added
- 【business-logic-hunt】新增业务逻辑审计/漏洞猎人 skill：双向核对（白皮书/需求文档/计划 vs 代码）找未实现、实现不一致、代码多于文档的缺口，再用六类清单（规则缺口/越权 IDOR/数值限额/状态机/并发事务/安全面）兜底；产出带证据链与分级的审计报告，**只查不改**，结尾必问「是否修复 / 是否补文档」
- 【business-logic-reqdoc】新增现状反写需求文档 skill：把已实现的业务逻辑抽成业务方可评审、其他 AI 可自行实现的**业务契约**；正文零实现标识（不写字段名/类名/接口路径），另单列「实现本需求的前提条件」
- 【business-logic-extractor】新增业务逻辑抽取器 skill（独立版）：从现有前后端代码抽取技术栈无关、AI 可读的可移植规格文档，附 5 份 references 与 `scripts/code-scanner.py`；同时补齐 `business-logic-init` 中对 `business-logic-extractor` 的引用
- 【plugin】`plugin.json` / `marketplace.json` / `README.md` 同步登记上述三个新 skill

### Changed
- 【business-logic-init / business-logic-improve / business-logic-execute】三份 SKILL.md 以其本地工作源（桌面 `business-logic/`）为准整体覆盖
- 【plugin】`marketplace.json` 描述与 `plugin.json` 对齐（原先落后，未含业务逻辑工作流）

## [1.3.0] - 2026-08-25

### Added
- 【skill-release-manager】新增「更新 skill」流：改 skill 内容时自动路由到 skill-creator 或 superpowers:writing-skills 进行内容更新，改完接回发版流
- 【skill-release-manager】description 补「编辑/改动 skill 内容」触发词；新增更新已存在 skill 的注意事项

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
