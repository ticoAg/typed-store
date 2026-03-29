# TypedStore

- Status: active
- Owner: mixed
- Spec: docs/design-spec.md
- Code SSOT: `typed_store/`, `tests/`, `examples/`, `pyproject.toml`
- Last Updated: 2026-03-29

## Goal

- 将 `TypedStore` 收口为面向外部发布的 protocol-first typed data access SDK
- 让 capability protocols、request objects 和 bind-first model surface 成为稳定 public API

## Current State

- `v0.2` 的 bind-first API 已落地并合并到主线
- `v0.3` 正在收口 capability protocols 和 request objects
- `QuerySpec`、内联 filter public surface、`store.of()`、默认 store helpers 已移除
- 当前 public 心智模型是 `SyncTypedStore` / `AsyncTypedStore` + `Model.bind(store)`

## Done

- 建立工作区级 `AGENTS first` 规则体系
- 建立 `docs/internal/workflow.md` 作为恢复与推进真源
- 建立 `docs/design-spec.md` 与 `docs/api-surface.md`
- 实现 engine / session / unit of work 基础设施
- 实现 `SyncTypedStore` / `AsyncTypedStore`
- 实现 `TypedStore` composition root
- 实现 `TypedStoreModel.bind(store)` 与 `bound_model.py`
- 增加显式生命周期 API：`close()` / `dispose()` / `aclose()`
- 移除默认 store helpers、`TypedStore` sync delegate 与 `store.of()`
- 实现 `typed_store/protocols.py`
- 实现 `typed_store/specs.py`
- 删除 `typed_store/query_spec.py`
- 删除 `typed_store/model_store.py`
- 将查询和变更收口到 `Query` / `PageRequest` / `Patch` / `ProjectionQuery`
- 重写主路径测试、错误边界测试、smoke tests、protocol tests
- 重写 README 和 examples 到 bind-first + request-object 心智模型
- 配置并验证 `ruff` / `ty` / `pytest` / `uv build` 工具链

## Next

- 完成 `v0.3` 全量验证并合并
- 评估 `update()` / `delete()` 的 SQL 级 bulk 语义是否需要进入下一阶段
- 补更完整的外部集成文档，例如 FastAPI / repository / transaction 场景
- 配置并验证仓库侧 Trusted Publisher（PyPI / TestPyPI）

## Evidence

- `typed_store/protocols.py`
- `typed_store/specs.py`
- `typed_store/sync.py`
- `typed_store/async_store.py`
- `typed_store/model.py`
- `typed_store/bound_model.py`
- `typed_store/store.py`
- `README.md`
- `docs/api-surface.md`
- `docs/design-spec.md`
- `examples/sync_basic.py`
- `examples/async_basic.py`
- `examples/repository_pattern.py`
- `examples/async_repository_pattern.py`
- `examples/model_mixin.py`
- `examples/model_store_view.py`
- `tests/test_specs.py`
- `tests/test_protocols.py`
- `tests/test_sync_store.py`
- `tests/test_async_store.py`
- `tests/test_bound_model.py`
- `tests/test_error_boundaries.py`
- `tests/test_examples.py`

## Risks / Blockers

- `update()` / `delete()` 仍然是 ORM-object mutation/remove 语义，不是 SQL bulk mutation
- `ProjectionQuery[TRow]` 的返回类型主要依赖调用方声明的投影形状与静态类型约束
- release workflow 依赖 PyPI Trusted Publisher 和 GitHub environment 预配置；未配置前无法真正完成发布
