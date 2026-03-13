---
trigger: always_on
---

请优先读取仓库根目录 `AGENTS.md`，并将其视为当前工作区规则真源。

恢复任务时，按以下顺序重建上下文：

1. `AGENTS.md`
2. `docs/internal/workflow.md`
3. `README.md`
4. `docs/design-spec.md`
5. `docs/internal/progress.md`
6. 相关代码与测试

核心要求：

- AGENTS first
- 代码作为 SSOT
- 研发进度通过 `docs/internal/progress.md` 持续追踪
- 工作流与恢复规则以 `docs/internal/workflow.md` 为准
