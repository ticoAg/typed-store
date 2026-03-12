# Docs Index

本目录承载当前工作区的长期文档，不直接复刻代码实现，而是用于组织以下内容：

- 架构与边界
- 主题级设计与需求
- 与研发流程相关的长期结论

## Layout

- `architecture/`：长期有效的工作区架构、边界、设计原则
- `specs/`：单主题需求、范围、设计、非目标、验收口径

## Authoring Rules

- 文档优先解释 why / scope / flow / verification
- 行为与实现细节以代码为 SSOT
- 需要长期保留的结论写入 `docs/`
- 主题推进状态写入 `todo/`，不要把动态进度写进这里

## Current Topics

- `specs/typed-store.md`：`TypedStore` SDK 的定位、架构、里程碑与验证策略。
