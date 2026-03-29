# TypedStore Public SDK v1.0 Design

## Overview

`v1.0` 的目标不是继续扩张 `TypedStore` 的能力边界，而是把当前已经成型的 protocol-first public SDK 收口为一个可稳定发布的版本。

这一版的完成定义是：

- public API 稳定
- release-ready
- bulk mutation 作为正式 public capability 落地

本设计延续已经确认的方向：

- `protocol first`
- 数据校验只在系统边界做一次
- 模型能力是一等能力，但只通过 `Model.bind(store)` 暴露
- sync / async 路径保持明确分离
- 不为旧设计保留兼容层

## Goals

- 将 `TypedStore` 收口为一个发布就绪的 public SDK
- 明确 `v1.0` 的稳定 public surface
- 正式引入 SQL 级 `bulk_update` / `bulk_delete`
- 保持 store 与绑定后模型视图两条主路径对 bulk capability 的一致支持
- 统一代码、类型、测试、文档、examples、打包与发布口径

## Non-goals

- 不在 `v1.0` 引入额外兼容层来保留旧 API
- 不把 `v1.0` 扩展成完整生态集成版，例如 FastAPI 全套指南
- 不在 SDK 内加入新的运行时数据校验管线
- 不把 bulk mutation 设计成可切换策略的单一 `update()` / `delete()`
- 不在本版引入完整 compatibility policy 文档

## Completion Definition

`v1.0` 完成时，仓库必须满足以下硬条件：

- `SyncTypedStore`、`AsyncTypedStore`、`TypedStoreModel.bind(store)`、capability protocols、request objects 进入稳定 public surface
- `bulk_update` / `bulk_delete` 成为正式 public API
- README、API surface、设计文档、发布文档与实现一致
- 包元数据、构建产物与 release workflow 达到发布就绪状态
- 主线验证矩阵固定并全部通过：
  - `uv run pytest`
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run ty check`
  - `uv build`

## Public API Freeze

### Stable public objects

`v1.0` 稳定面包括：

- `SyncTypedStore`
- `AsyncTypedStore`
- `TypedStore`
- `TypedStoreModel`
- `SyncBoundModelView`
- `AsyncBoundModelView`
- sync / async capability protocols
- `Query`
- `PageRequest`
- `Patch`
- `ProjectionQuery`
- `Page`
- `UnitOfWork`
- `AsyncUnitOfWork`
- `SessionProvider`

### Explicitly non-stable implementation details

以下内容不属于 `v1.0` 稳定 public contract：

- SQLAlchemy 适配实现细节
- 内部辅助函数与私有逻辑
- 文档未明确导出的内部约定
- 未来可能调整的内部 statement 构建细节

### Public API principles

- 主路径保持显式：先选 sync / async store，再按需绑定模型
- 不恢复默认 store helpers、`store.of()`、内联 filter public signatures
- public API 以 capability protocols 和 request objects 为核心，而不是以 facade 语法糖为核心

## Bulk Mutation Design

### Public API shape

bulk mutation 采用独立方法，而不是在 `update()` / `delete()` 上引入模式参数。

store 层：

- `bulk_update(model, *, query, patch, session=None, commit=True) -> int`
- `bulk_delete(model, *, query, session=None, commit=True) -> int`

模型绑定视图层：

- `Model.bind(store).bulk_update(*, query, patch, session=None, commit=True) -> int`
- `Model.bind(store).bulk_delete(*, query, session=None, commit=True) -> int`

返回值统一为受影响行数。

### Semantic split

`v1.0` 明确保留两套 mutation 语义：

- `update()` / `delete()`
  - 通过 ORM object 路径执行
  - 加载对象后修改或删除
  - 适合需要 ORM 对象语义的场景

- `bulk_update()` / `bulk_delete()`
  - 通过 SQLAlchemy `update()` / `delete()` 语句直接执行
  - 不加载 ORM 对象
  - 不依赖 identity map
  - 适合明确的批量写路径

这两条路径必须在 API surface、README、examples、tests 中被清楚区分。

### Relationship with request objects

bulk mutation 继续复用现有 request objects：

- `bulk_update(..., query=Query[T], patch=Patch[T])`
- `bulk_delete(..., query=Query[T])`

但 `bulk` 路径只接受具有安全 SQL 语义的 `Query` 形态。对于以下字段：

- `order_by`
- `limit`
- `offset`
- `options`

`v1.0` 采用严格模式：若调用方在 bulk 路径上传入这些字段，则抛出明确 contract error，而不是静默忽略。

这样做的原因是：

- bulk mutation 的语义必须可预测
- `v1.0` 不适合接受“部分字段被忽略”的隐式行为
- 这符合“仅保留必要的 contract/configuration 级运行时保护”

### Protocol changes

`v1.0` 需要新增 bulk capability protocols，并保持 sync / async 分离：

- `BulkPatchableStoreProtocol[T]`
- `BulkDeletableStoreProtocol[T]`
- `AsyncBulkPatchableStoreProtocol[T]`
- `AsyncBulkDeletableStoreProtocol[T]`

同时更新 composite model-bound protocols，使绑定后的模型视图天然拥有 bulk capability。

### Error handling

bulk 路径保留以下运行时保护：

- `Query` 含有 bulk 不支持的字段时抛明确错误
- sync / async session factory 缺失
- 模型绑定传入不满足协议的 store
- 明显的 contract violation

SDK 不在 bulk 路径上重复做业务数据值级校验。

## Release-Ready Requirements

### Package and metadata

`v1.0` 必须确认以下分发语义：

- `pyproject.toml` 中的 package metadata 面向外部发布完整可用
- `README.md` 可作为 long description
- `py.typed` 正确包含在发行产物中
- `uv build` 生成的 sdist / wheel 可用

### Publishing path

以下内容必须口径一致：

- `docs/publishing.md`
- GitHub release workflow
- 当前仓库中的包名、版本、产物路径

### Documentation quality

`v1.0` 需要让文档承担真正的对外发布职责，而不是只做方向说明：

- `README.md`：最小主路径与 onboarding
- `docs/api-surface.md`：完整稳定 public contract
- `docs/design-spec.md`：语义边界与设计原则
- `docs/publishing.md`：发布路径与要求
- `docs/internal/progress.md`：更新为 `v1.0` 收口状态

## Examples and Onboarding

examples 在 `v1.0` 不只是 smoke test 输入，还要承担 onboarding 职责。

最少覆盖：

- sync basic
- async basic
- repository pattern
- async repository pattern
- bind-first model usage
- bulk update / bulk delete 示例

要求：

- 示例代码必须反映最终 public API
- 示例不使用旧心智模型
- README 与 examples 之间的调用方式保持一致

## Architecture Impact

### Store layer

`SyncTypedStore` / `AsyncTypedStore` 需要：

- 实现 bulk capability protocols
- 用 SQLAlchemy 原生 `update()` / `delete()` 执行 bulk mutation
- 在已有的 object-based mutation 路径之外提供明确分离的新 API

### Bound model view layer

`SyncBoundModelView` / `AsyncBoundModelView` 需要：

- 将 `bulk_update` / `bulk_delete` 路由到 store capability
- 保持与现有 `insert / find / update / delete` 一致的模型优先体验

### Error layer

需要新增或扩展明确的 contract errors，用于表达：

- bulk mutation 不支持的 query 形态
- bulk 与 request object 组合不合法

## Validation Matrix

`v1.0` 的最小验证矩阵固定为：

| Area | Validation |
|---|---|
| Bulk capability behavior | `uv run pytest` |
| Public API typing | `uv run ty check` |
| Static quality | `uv run ruff check .` |
| Formatting | `uv run ruff format --check .` |
| Distribution | `uv build` |
| Release readiness | 文档与 workflow 路径自检 |

## Task Breakdown

### Task 1: Bulk mutation capability

- 新增 bulk capability protocols
- 在 sync / async stores 上实现 `bulk_update` / `bulk_delete`
- 在 sync / async bound model views 上暴露 bulk 方法
- 增加 bulk contract error 与测试

### Task 2: Public API freeze

- 收口 `typed_store/__init__.py`
- 明确稳定导出面
- 明确哪些对象属于 public surface
- 更新 API surface 文档中的稳定性说明

### Task 3: Release-ready packaging and publishing

- 检查 `pyproject.toml`
- 检查 `py.typed` 分发语义
- 对齐 `README.md`、`docs/publishing.md`、release workflow
- 确认构建与发布路径一致

### Task 4: Examples, docs, tests sync

- 新增 bulk examples
- 更新 README 主路径
- 补 bulk 相关测试与 smoke coverage
- 更新 progress 文档到 `v1.0` 语境

## Out of Scope

以下内容不纳入本次 `v1.0`：

- 完整 FastAPI / Starlette 集成指南
- cursor pagination
- 更复杂的 projection typing 扩展
- 完整 semver / deprecation policy 文档
- 额外后端实现

## References

- `docs/design-spec.md`
- `docs/api-surface.md`
- `docs/publishing.md`
- `docs/internal/progress.md`
- `typed_store/protocols.py`
- `typed_store/specs.py`
- `typed_store/sync.py`
- `typed_store/async_store.py`
- `typed_store/model.py`
- `typed_store/bound_model.py`
