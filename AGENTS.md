---
language: zh
type: AI Agent Guidance (Workspace-Level)
note: Shared rules for the current workspace and all future child projects.
---

# Workspace Guidelines

本文件作用域覆盖当前工作目录 `./**`，目标是把这里作为一个“AGENTS first、代码为 SSOT、研发过程可恢复可追踪”的工作区来使用。

当前仓库允许随着后续开发逐步承载多个子项目、工具、实验目录或交付物，但默认不把它们视为彼此孤立的散乱文件夹。工作区规则负责定义“怎么协作、怎么恢复、怎么追踪”；具体实现与技术细节则下沉到各自代码与文档真源。

## 1. Workspace Objectives

本工作区优先满足以下目标：

- `AGENTS first`：任何进入仓库开展工作的 agent，先读规则，再读工作流，再读目标模块文档。
- `Code as SSOT`：代码与测试是行为真源；文档负责解释边界、意图、流程与进度，不复制实现细节。
- `Traceable progress`：每个进行中的主题都应能快速回答“目标是什么、做到哪了、下一步是什么、证据在哪”。
- `Recoverable workflow`：任务中断后，下一位人或 agent 能低成本恢复上下文。
- `Small diffs`：尽量以小步、可验证、可回滚的增量推进，而不是大爆炸式重构。

## 2. Initialization Order

进入当前工作区后，默认按以下顺序建立上下文：

1. `./AGENTS.md`
2. `./workflow.md`
3. `./README.md`
4. 目标子目录中的 `README.md` / `AGENTS.md`（若存在）
5. 与任务直接相关的 `docs/`、`todo/`、代码和测试

补充约定：

- 若任务只涉及工作区治理、协作方式、目录结构或研发流程，优先更新 `./AGENTS.md` 与 `./workflow.md`。
- 若任务涉及具体模块实现，先判断该模块是否已有自己的 `README.md`、`AGENTS.md`、`docs/specs/*` 或 `todo/*`。
- 若模块规则与工作区规则冲突，以更深层目录中的 `AGENTS.md` 为准；若与用户明确指令冲突，以用户指令为准。

## 3. Single Sources of Truth

工作区采用以下 SSOT 约定：

- 行为与实现真源：代码、测试、可运行脚本
- 协作与恢复真源：`./workflow.md`
- 工作区级规则真源：`./AGENTS.md`
- 架构与边界真源：`./docs/architecture/*.md`
- 特性需求与设计真源：`./docs/specs/<topic>.md`
- 研发进度与待办真源：`./todo/*.md`

原则：

- 不在多个地方重复维护同一条规则。
- 文档解释 why / scope / flow / progress，不复刻代码实现。
- 若文档与代码不一致，优先指出偏差，并以代码现状为行为真源，再决定修代码还是修文档。
- 需求、设计、待办、进度必须能反向链接到代码、测试、脚本或路径证据。

## 4. AGENTS-first Rules

### 4.1 Rules before implementation

- 在动手实现前，先确认当前规则、工作流、主目录边界和真源位置。
- 若需要新增子项目或模块，先补对应目录的 `README.md`，必要时补该目录的 `AGENTS.md`。
- 若需要新增长期有效的协作规则，优先落在 `AGENTS.md`，不要把规则散落进临时任务文档。

### 4.2 Distinguish rules vs plans vs progress

- `AGENTS.md`：长期有效的规则与协作约定
- `workflow.md`：任务如何开始、推进、验证、恢复、交接
- `docs/specs/*.md`：某个主题的需求、范围、设计、验收口径
- `todo/*.md`：某个主题当前进展、证据、剩余动作、阻塞项

不要混用：

- 不把长期规则写进某个单次任务 TODO
- 不把短期进度写进 `AGENTS.md`
- 不把实现细节堆满 `workflow.md`

## 5. Code as SSOT

### 5.1 What code owns

以下内容默认以代码为真源：

- 实际行为、分支逻辑、默认值
- 对外接口与入参结构
- 数据模型、类型定义、状态流转
- 测试可覆盖的约束与回归用例

### 5.2 What docs own

以下内容默认由文档承担：

- 模块边界与职责划分
- 需求背景与非目标
- 推荐阅读顺序与恢复路径
- 进度状态、风险、阻塞与待验证事项
- 跨模块关系与验证闭环

### 5.3 Documentation discipline

- 文档应引用代码路径、测试路径、脚本路径，而不是大段复制源码。
- 若描述 API 或类型，优先指向代码位置或生成文档入口。
- 若实现已变，先更新代码，再同步文档；不要反过来把旧文档当事实来源。

## 6. Progress Tracking Model

为保证研发进度便于追踪，当前工作区约定：

- 每个持续超过一次对话 / 一次提交周期的主题，都应有一份 `todo/<topic>.md`
- 每份 `todo/<topic>.md` 至少包含：目标、当前状态、已完成、下一步、证据、风险 / 阻塞
- 每个需要较强设计约束的主题，配套一份 `docs/specs/<topic>.md`
- `todo/README.md` 作为总索引，列出 active / proposed / blocked / done 主题

推荐状态：

- `proposed`
- `active`
- `blocked`
- `done`
- `archived`

## 7. Change Strategy

- 先定主改动区域，再动手。
- 优先改真源位置，不先在消费侧打补丁。
- 每次改动尽量附带最小验证路径。
- 大改前先补设计文档或任务文档，再实现。
- 若当前改动会影响工作流或协作边界，必须同步更新 `AGENTS.md`、`workflow.md` 或相关 docs。

## 8. Verification Strategy

- 优先做与改动层级匹配的最小验证。
- 文档类变更至少验证路径、自引用、阅读顺序和命名自洽。
- 实现类变更至少给出可复现命令、测试入口或手动验证路径。
- 无法验证时，必须明确说明缺少什么依赖、使用了什么替代验证、残余风险是什么。

## 9. Recovery and Handoff

任务中断后，恢复上下文时按以下顺序：

1. `./AGENTS.md`
2. `./workflow.md`
3. `./README.md`
4. 对应主题的 `docs/specs/<topic>.md`
5. 对应主题的 `todo/<topic>.md`
6. 相关代码、测试、脚本和最近改动

恢复时优先回答：

- 当前主题是什么？
- 真源代码在哪里？
- 现在做到哪一步了？
- 下一步最小动作是什么？
- 还有哪些风险、阻塞或未验证项？

## 10. Delivery Expectations

最终交付优先说明：

- 主改动区域
- 改了什么
- 为什么这么设计
- 如何验证
- 当前状态与下一步

若本次改动影响了工作流、规则或进度追踪方式，应明确指出已更新 `AGENTS.md`、`workflow.md`、`docs/` 或 `todo/` 中的哪些文件。
