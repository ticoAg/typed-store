# API Surface

本文档描述 `TypedStore` 当前对外推荐的 public API。目标是让使用者快速判断：

- 从哪里进入
- store capability protocol 和 concrete store 的关系
- request objects 应该如何驱动查询、分页、更新和投影

## 1. Primary Entry Points

当前推荐的主入口只有四类：

- `SyncTypedStore`：同步 SQLAlchemy 路径的正式实现
- `AsyncTypedStore`：异步 SQLAlchemy 路径的正式实现
- `TypedStoreModel.bind(store)`：模型一等能力的绑定入口
- `TypedStore`：只负责组合 `.sync` / `.async_` 的 composition root

## 2. Request Objects

`TypedStore` 的查询与变更都由显式 request objects 驱动，而不是内联 filter 参数。

### `Query[TModel]`

用于实体查询：

- `Query[TModel]()`：创建空查询
- `.where(*filters)`：追加过滤条件
- `.order(*clauses)`：追加排序
- `.limit_to(limit)`：设置 limit
- `.offset_by(offset)`：设置 offset
- `.with_options(*options)`：追加 SQLAlchemy loader options

### `PageRequest`

用于分页请求：

- `PageRequest(limit, offset=0)`

### `Patch[TModel]`

用于字段级更新：

- `Patch[TModel](values={"field": value})`

### `ProjectionQuery[TRow]`

用于显式列投影：

- `ProjectionQuery[TRow](*columns)`
- `.where(*filters)`
- `.order(*clauses)`
- `.with_options(*options)`

## 3. Sync Capability Protocols

同步 capability protocol 定义 public contract：

- `ReadableStoreProtocol[TModel]`
- `WritableStoreProtocol[TModel]`
- `PatchableStoreProtocol[TModel]`
- `BulkPatchableStoreProtocol[TModel]`
- `DeletableStoreProtocol[TModel]`
- `BulkDeletableStoreProtocol[TModel]`
- `StatementExecutorProtocol`
- `TransactionalStoreProtocol`
- `SyncModelBoundStoreProtocol[TModel]`

这些协议的意义是定义“这个对象能做什么”，而不是要求使用者必须直接实例化协议本身。
这些对象共同构成 `v1.0` 的稳定同步 public contract。

## 4. Async Capability Protocols

异步路径与同步路径保持明确分离，对应协议为：

- `AsyncReadableStoreProtocol[TModel]`
- `AsyncWritableStoreProtocol[TModel]`
- `AsyncPatchableStoreProtocol[TModel]`
- `AsyncBulkPatchableStoreProtocol[TModel]`
- `AsyncDeletableStoreProtocol[TModel]`
- `AsyncBulkDeletableStoreProtocol[TModel]`
- `AsyncStatementExecutorProtocol`
- `AsyncTransactionalStoreProtocol`
- `AsyncModelBoundStoreProtocol[TModel]`

这些对象共同构成 `v1.0` 的稳定异步 public contract。

## 5. `SyncTypedStore`

`SyncTypedStore` 是基于 SQLAlchemy `Session` 的同步实现。

### Factory And Lifecycle

- `SyncTypedStore.from_url(url, *, echo=False, **engine_options)`
- `.engine`
- `.close()`
- `.dispose()`
- `.unit_of_work(*, auto_commit=True)`

### CRUD And Query Methods

- `insert(entity, *, session=None, commit=True, refresh=False) -> TModel`
- `insert_many(entities, *, session=None, commit=True) -> list[TModel]`
- `get(model, ident, *, session=None) -> TModel | None`
- `find_one(model, *, query, session=None) -> TModel | None`
- `find_many(model, *, query, session=None) -> list[TModel]`
- `exists(model, *, query, session=None) -> bool`
- `count(model, *, query, session=None) -> int`
- `paginate(model, *, query, page, session=None) -> Page[TModel]`
- `update(model, *, query, patch, session=None, commit=True) -> int`
- `bulk_update(model, *, query, patch, session=None, commit=True) -> int`
- `delete(model, *, query, session=None, commit=True) -> int`
- `bulk_delete(model, *, query, session=None, commit=True) -> int`
- `select_rows(model, *, projection, session=None) -> list[TRow]`
- `select_scalars(statement, *, session=None) -> list[TScalar]`

### Example

```python
from typed_store import PageRequest, Query, SyncTypedStore

store = SyncTypedStore.from_url("sqlite:///app.db")

admins = store.find_many(
    User,
    query=Query[User]().where(User.role == "admin").order(User.id.asc()),
)

page = store.paginate(
    User,
    query=Query[User]().where(User.role == "admin").order(User.id.asc()),
    page=PageRequest(limit=20, offset=0),
)
```

## 6. `AsyncTypedStore`

`AsyncTypedStore` 是基于 SQLAlchemy `AsyncSession` 的异步实现。

### Factory And Lifecycle

- `AsyncTypedStore.from_url(url, *, echo=False, **engine_options)`
- `.engine`
- `.aclose()`
- `.dispose()`
- `.unit_of_work(*, auto_commit=True)`

### CRUD And Query Methods

签名与 `SyncTypedStore` 对称，但所有行为都是 `async def`。

### Example

```python
from typed_store import AsyncTypedStore, PageRequest, Query

store = AsyncTypedStore.from_url("sqlite+aiosqlite:///app.db")

items = await store.find_many(
    User,
    query=Query[User]().where(User.role == "admin"),
)

page = await store.paginate(
    User,
    query=Query[User]().where(User.role == "admin").order(User.id.asc()),
    page=PageRequest(limit=20, offset=0),
)
```

## 7. `TypedStore`

`TypedStore` 是 composition root，不是直接 CRUD facade。

### Surface

- `TypedStore.from_url(url=None, *, async_url=None, echo=False, **engine_options)`
- `.engine`
- `.async_engine`
- `.sync`
- `.async_`
- `.close()`
- `.dispose()`
- `.aclose()`
- `.unit_of_work(*, auto_commit=True)`
- `.async_unit_of_work(*, auto_commit=True)`

### Example

```python
from typed_store import Query, TypedStore

ts = TypedStore.from_url("sqlite:///app.db", async_url="sqlite+aiosqlite:///app.db")

ts.sync.find_many(User, query=Query[User]())
await ts.async_.find_many(User, query=Query[User]())
```

## 8. `TypedStoreModel.bind(store)`

模型能力是一等 public API，但只有绑定后才可操作。

### Rules

- 只有 `bind(store)`，没有隐式默认 store
- `bind()` 是纯函数式绑定，不会把 store 写回模型类
- sync model view 依赖 sync capability protocols
- async model view 依赖 async capability protocols

### Bound Model Methods

`Model.bind(store)` 返回的 bound model view 提供：

- `insert`
- `insert_many`
- `get`
- `find_one`
- `find_many`
- `exists`
- `count`
- `paginate`
- `update`
- `bulk_update`
- `delete`
- `bulk_delete`

### Example

```python
from typed_store import PageRequest, Patch, Query

users = User.bind(store)

items = users.find_many(
    query=Query[User]().where(User.role == "admin").order(User.id.asc()),
)

updated = users.update(
    query=Query[User]().where(User.email == "alice@example.com"),
    patch=Patch[User]({"role": "staff"}),
)

page = users.paginate(
    query=Query[User]().where(User.role == "staff"),
    page=PageRequest(limit=10, offset=0),
)
```

## 9. Error Boundary

当前 public API 的运行时保护只保留 contract/configuration 级错误：

- 缺失 sync / async session factory
- `bind()` 传入不满足协议的 store
- bulk mutation 使用了不支持的 `Query` 形态
- 调用签名明显错误，例如遗漏 `projection=` 这样的关键字参数

数据本身的业务校验不由 `TypedStore` 重复承担，默认依赖边界层与静态类型系统。

## 10. Stable v1.0 Surface

以下对象属于 `v1.0` 稳定 public API：

- stores: `SyncTypedStore`, `AsyncTypedStore`, `TypedStore`
- models: `TypedStoreModel`, `SyncBoundModelView`, `AsyncBoundModelView`
- request objects: `Query`, `PageRequest`, `Patch`, `ProjectionQuery`
- results: `Page`
- protocols: readable / writable / patchable / bulk / deletable / statement / transactional variants
- support objects: `UnitOfWork`, `AsyncUnitOfWork`, `SessionProvider`
