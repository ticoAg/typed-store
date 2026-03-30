# TypedStore

- Status: active
- Owner: mixed
- Spec: docs/design-spec.md
- Code SSOT: `typed_store/`, `tests/`, `examples/`, `pyproject.toml`
- Last Updated: 2026-03-30

## Goal

- 将 `TypedStore` 收口为面向外部发布的 protocol-first typed data access SDK
- 让 capability protocols、request objects 和 bind-first model surface 成为稳定 public API

## Current State

- `v1.0` public API freeze 与 release-ready 收口正在进行
- bulk mutation 已作为一等 public capability 进入当前实现
- 旧查询对象、内联 filter public surface、旧模型快捷入口、默认 store helpers 已移除
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
- 移除默认 store helpers、`TypedStore` sync delegate 与旧模型快捷入口
- 实现 `typed_store/protocols.py`
- 实现 `typed_store/specs.py`
- 删除 `typed_store/query_spec.py`
- 删除 `typed_store/model_store.py`
- 将查询和变更收口到 `Query` / `PageRequest` / `Patch` / `ProjectionQuery`
- 重写主路径测试、错误边界测试、smoke tests、protocol tests
- 重写 README 和 examples 到 bind-first + request-object 心智模型
- 配置并验证 `ruff` / `ty` / `pytest` / `uv build` 工具链
- 新增 bulk mutation contract 与 sync / async / bound model 主路径测试

## Next

- 收口 `v1.0` 稳定导出面
- 对齐 `py.typed`、包元数据与 release workflow
- 增加 bulk onboarding 示例并完成全量发布前验证

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

- `ProjectionQuery[TRow]` 的返回类型主要依赖调用方声明的投影形状与静态类型约束
- release workflow 依赖 PyPI Trusted Publisher 和 GitHub environment 预配置；未配置前无法真正完成发布
