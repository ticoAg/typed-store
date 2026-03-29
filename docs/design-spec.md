# TypedStore

## Overview

`TypedStore` 是构建在 SQLAlchemy 2.x 之上的 protocol-first typed data access SDK。

当前设计目标不是包装出另一个 ORM，而是把数据访问能力收口成稳定的 public contract：

- capability protocols 负责定义“可以做什么”
- request objects 负责表达“这次要怎么做”
- sync / async 路径保持明确分离
- 模型能力通过 `Model.bind(store)` 暴露，而不是依赖隐式全局状态

## Goals

- 以 public SDK 的标准收敛 API，而不是继续堆叠内部 helper
- 用 capability protocols 作为设计骨架
- 用 `Query` / `PageRequest` / `Patch` / `ProjectionQuery` 作为唯一推荐请求对象
- 维持 SQLAlchemy-native 的表达能力，不重造 DSL
- 只在 contract/configuration 边界做最少运行时保护

## Non-goals

- 不替代 SQLAlchemy 的映射和表达式系统
- 不继续保留 `QuerySpec`、内联 filter 参数或默认 store 兼容层
- 不把事务、查询、模型绑定、副作用初始化混成一个大 facade
- 不在 SDK 内重复做业务数据校验

## Positioning

`TypedStore` 的定位是：

- 面向外部发布的通用 SDK
- SQLAlchemy 之上的 typed data access layer
- 适用于 repository、service、脚本和模型优先的数据访问

## Design Principles

### Protocol first

- 先定义能力协议，再让 concrete store 去实现
- public API 依赖协议与 request objects，而不是依赖隐式约定

### Boundary-only validation

- 数据在边界处校验一次即可
- SDK 内部默认信任已经构造好的 request objects
- 运行时只保留少量 configuration / contract violation 检查

### Explicit sync / async split

- `SyncTypedStore` 和 `AsyncTypedStore` 分别实现独立协议
- `TypedStore` 只做 composition root

### Bind-first model capability

- 模型能力是一等能力
- 只有 `Model.bind(store)`，没有类级默认 store
- `bind()` 是纯函数式绑定，不在模型类上保存状态

### SQLAlchemy-native

- 过滤、排序、loader options 继续直接使用 SQLAlchemy expressions / options
- 自定义语句仍可通过 `select_scalars()` 等 escape hatch 执行

## Target Architecture

```mermaid
flowchart TB
    App[Apps / Services / Scripts] --> SyncStore[SyncTypedStore]
    App --> AsyncStore[AsyncTypedStore]
    App --> Model[TypedStoreModel.bind(store)]
    App --> Bundle[TypedStore]

    SyncStore --> SyncProtocols[Sync capability protocols]
    AsyncStore --> AsyncProtocols[Async capability protocols]
    Model --> BoundView[Bound model view]

    SyncProtocols --> Requests[Query / PageRequest / Patch / ProjectionQuery]
    AsyncProtocols --> Requests
    BoundView --> SyncProtocols
    BoundView --> AsyncProtocols

    SyncStore --> SA[SQLAlchemy 2.x]
    AsyncStore --> SA
    SA --> DB[(Database)]
```

## Implemented Package Layout

```text
./typed_store/
  __init__.py
  async_store.py
  bound_model.py
  engine.py
  errors.py
  model.py
  protocols.py
  results.py
  session.py
  specs.py
  store.py
  sync.py
  uow.py
```

说明：

- `protocols.py` 定义 capability contracts
- `specs.py` 定义 immutable request objects
- `sync.py` / `async_store.py` 提供 SQLAlchemy adapters
- `model.py` / `bound_model.py` 提供 bind-first model surface
- `store.py` 只保留 composition root 角色

## Core Concepts

### Capability protocols

同步与异步路径分别定义：

- readable
- writable
- patchable
- deletable
- statement executor
- transactional
- model-bound composite protocol

协议层是 public contract，concrete stores 是标准实现。

### Request objects

#### `Query[TModel]`

表达实体查询：

- filters
- order
- limit
- offset
- loader options

#### `PageRequest`

表达分页请求：

- limit
- offset

#### `Patch[TModel]`

表达字段更新：

- `values`

#### `ProjectionQuery[TRow]`

表达显式投影：

- columns
- filters
- order
- loader options

### Result types

当前结果形态保持稳定：

- `get(model, ident)` -> `TModel | None`
- `find_one(model, *, query)` -> `TModel | None`
- `find_many(model, *, query)` -> `list[TModel]`
- `paginate(model, *, query, page)` -> `Page[TModel]`
- `select_rows(model, *, projection)` -> `list[TRow]`
- `select_scalars(statement)` -> `list[TScalar]`
- `update(model, *, query, patch)` -> `int`
- `delete(model, *, query)` -> `int`

### TypedStoreModel

模型层规则如下：

- 继承 `TypedStoreModel` 的模型天然支持 `bind(store)`
- 绑定后获得 bound model view
- bound model view 只路由 capability protocol，不自己决定事务策略

## Implementation Status

当前已实现：

- `SyncTypedStore` / `AsyncTypedStore` 的 protocol-first CRUD surface
- `TypedStore` composition root
- `TypedStoreModel.bind(store)` 与 bound model views
- capability protocols
- `Query` / `PageRequest` / `Patch` / `ProjectionQuery`
- `Page`
- unit of work
- examples、smoke tests、error boundary tests、protocol tests

当前明确移除：

- `QuerySpec`
- 内联 filter public method signatures
- 默认 store helpers
- `store.of()` 和旧 `model_store.py`
- `TypedStore` 直接 CRUD delegate

## Validation

当前最低验证矩阵：

| 改动类型 | 最低验证 |
|---|---|
| protocol / store surface | `uv run pytest` |
| 类型契约 | `uv run ty check` |
| 静态风格 | `uv run ruff check .` |
| 格式一致性 | `uv run ruff format --check .` |
| 可发布性 | `uv build` |

## References

- `AGENTS.md`
- `docs/internal/workflow.md`
- `docs/api-surface.md`
- `docs/internal/progress.md`
- `typed_store/protocols.py`
- `typed_store/specs.py`
- `typed_store/sync.py`
- `typed_store/async_store.py`
- `typed_store/model.py`
- `typed_store/bound_model.py`
- `examples/sync_basic.py`
- `examples/async_basic.py`
- `examples/model_mixin.py`
- `examples/model_store_view.py`
- `tests/test_protocols.py`
- `tests/test_specs.py`
- `tests/test_error_boundaries.py`
