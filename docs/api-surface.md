# API Surface

本文档概述 `TypedStore` 当前对外推荐使用的 API surface，目的是帮助使用者快速判断：

- 应该从哪个入口开始
- 不同对象分别负责什么
- 哪些场景适合 facade，哪些场景适合 mixin 或 repository

## 1. Primary entry points

当前推荐的主要入口有三类：

- `SyncTypedStore` — 同步代码路径的主入口
- `AsyncTypedStore` — 异步代码路径的主入口
- `TypedStore` — bundle，同时暴露 `.sync` / `.async_`，也可直接当 sync store 用

## 2. `SyncTypedStore`

职责：

- 面向同步 SQLAlchemy session 的 typed facade
- 封装插入、查询、分页、更新、删除等基础行为
- 提供同步 unit of work

### 工厂方法与属性

- `SyncTypedStore.from_url(url, *, echo=False, **engine_options)` — 一行初始化
- `.engine` — 返回底层 `Engine | None`
- `.of(model)` — 返回 `SyncModelStore[M]`，省去重复传 model 参数
- `.unit_of_work(*, auto_commit=True)` — 创建 `UnitOfWork`

### 数据操作方法

所有查询方法均支持内联参数（`*filters`, `order`, `limit`, `offset`），也可通过 `spec=QuerySpec(...)` 传入复杂查询。

- `insert(entity, *, session=None, commit=True, refresh=False)` → `TModel`
- `insert_many(entities, *, session=None, commit=True)` → `list[TModel]`
- `get(model, ident, *, session=None)` → `TModel | None`
- `find_one(model, *filters, spec=None, order=None, session=None)` → `TModel | None`
- `find_many(model, *filters, spec=None, order=None, limit=None, offset=None, session=None)` → `list[TModel]`
- `paginate(model, *filters, spec=None, order=None, limit=None, offset=None, session=None)` → `Page[TModel]`
- `update_fields(model, values, *filters, spec=None, session=None, commit=True)` → `int`
- `delete_where(model, *filters, spec=None, session=None, commit=True)` → `int`
- `select_rows(model, spec, *, session=None)` → `list[object]`
- `select_scalars(statement, *, session=None)` → `list[TScalar]`

### 使用示例

```python
from typed_store import SyncTypedStore

store = SyncTypedStore.from_url("sqlite:///app.db")
Base.metadata.create_all(store.engine)

store.insert(User(name="alice"))
store.find_many(User, User.role == "admin", order=User.id.asc())
store.paginate(User, User.role == "admin", limit=10, offset=0)
```

适用场景：脚本、同步服务层、repository 层、小型工具程序

## 3. `AsyncTypedStore`

职责：

- 面向异步 SQLAlchemy session 的 typed facade
- 在异步路径上提供与同步 facade 完全对称的 API
- 提供异步 unit of work

### 工厂方法与属性

- `AsyncTypedStore.from_url(url, *, echo=False, **engine_options)` — 一行初始化
- `.engine` — 返回底层 `AsyncEngine | None`
- `.of(model)` — 返回 `AsyncModelStore[M]`
- `.unit_of_work(*, auto_commit=True)` — 创建 `AsyncUnitOfWork`

### 数据操作方法

签名与 `SyncTypedStore` 完全对称，所有方法均为 `async def`：

- `insert(entity, *, session=None, commit=True, refresh=False)` → `TModel`
- `insert_many(entities, *, session=None, commit=True)` → `list[TModel]`
- `get(model, ident, *, session=None)` → `TModel | None`
- `find_one(model, *filters, spec=None, order=None, session=None)` → `TModel | None`
- `find_many(model, *filters, spec=None, order=None, limit=None, offset=None, session=None)` → `list[TModel]`
- `paginate(model, *filters, spec=None, order=None, limit=None, offset=None, session=None)` → `Page[TModel]`
- `update_fields(model, values, *filters, spec=None, session=None, commit=True)` → `int`
- `delete_where(model, *filters, spec=None, session=None, commit=True)` → `int`
- `select_rows(model, spec, *, session=None)` → `list[object]`
- `select_scalars(statement, *, session=None)` → `list[TScalar]`

### 使用示例

```python
from typed_store import AsyncTypedStore

store = AsyncTypedStore.from_url("sqlite+aiosqlite:///app.db")

await store.insert(User(name="alice"))
await store.find_many(User, User.role == "admin")
```

适用场景：FastAPI / Starlette 等 async 服务、异步任务执行器

## 4. `TypedStore`

职责：

- 同时暴露 `.sync` 和 `.async_` facade
- 可直接当 sync store 使用（所有 sync 方法均已委托）
- 异步操作通过 `.async_` 明确访问

### 工厂方法与属性

- `TypedStore.from_url(url=None, *, async_url=None, echo=False, **engine_options)` — 一行初始化
- `.engine` — 返回底层 sync `Engine | None`
- `.async_engine` — 返回底层 `AsyncEngine | None`
- `.sync` — `SyncTypedStore` 实例
- `.async_` — `AsyncTypedStore` 实例
- `.of(model)` — 返回 `SyncModelStore[M]`（委托到 `.sync`）
- `.unit_of_work(*, auto_commit=True)` — 创建 sync `UnitOfWork`
- `.async_unit_of_work(*, auto_commit=True)` — 创建 `AsyncUnitOfWork`

### Sync 委托方法

以下方法直接委托到 `.sync`，签名与 `SyncTypedStore` 一致：

- `insert`, `insert_many`, `get`, `find_one`, `find_many`, `paginate`
- `update_fields`, `delete_where`
- `select_rows`, `select_scalars`

### 使用示例

```python
from typed_store import TypedStore

ts = TypedStore.from_url("sqlite:///app.db", async_url="sqlite+aiosqlite:///app.db")

# 直接当 sync store 用
ts.find_many(User)
ts.insert(User(name="alice"))

# 异步明确走 .async_
await ts.async_.find_many(User)
```

## 5. `SyncModelStore` / `AsyncModelStore`

职责：

- Model-bound 子视图，省去每次调用都传 model 参数
- 通过 `store.of(Model)` 创建

### 方法

`SyncModelStore[TModel]` 和 `AsyncModelStore[TModel]` 提供完全对称的方法：

- `insert(entity, *, session=None, commit=True, refresh=False)` → `TModel`
- `insert_many(entities, *, session=None, commit=True)` → `list[TModel]`
- `get(ident, *, session=None)` → `TModel | None`
- `find_one(*filters, spec=None, order=None, session=None)` → `TModel | None`
- `find_many(*filters, spec=None, order=None, limit=None, offset=None, session=None)` → `list[TModel]`
- `paginate(*filters, spec=None, order=None, limit=None, offset=None, session=None)` → `Page[TModel]`
- `update_fields(values, *filters, spec=None, session=None, commit=True)` → `int`
- `delete_where(*filters, spec=None, session=None, commit=True)` → `int`

### 使用示例

```python
users = store.of(User)
users.insert(User(name="alice"))
users.find_many(User.role == "admin")
users.get(1)
users.paginate(limit=10)
```

## 6. `QuerySpec`

职责：

- 把查询意图组织成稳定的不可变对象
- 适合构建可复用的复杂查询

### 构造与链式方法

- `QuerySpec[TModel]()` — 创建空 spec
- `.where(*filters)` — 追加过滤条件
- `.order(*clauses)` — 设置排序
- `.paginate(limit=..., offset=...)` — 设置分页
- `.select_columns(*columns)` — 投影（仅选择特定列）
- `.with_options(*options)` — 附加 loader options
- `.build_select(model)` — 生成 SQLAlchemy `Select` 语句
- `.count_select(model)` — 生成计数用 `Select` 语句

### 使用示例

```python
from typed_store import QuerySpec

spec = (
    QuerySpec[User]()
    .where(User.role == "admin")
    .order(User.id.asc())
    .paginate(limit=10, offset=0)
)
store.find_many(User, spec=spec)
```

适用场景：repository 内构建可复用查询、在 service 层表达清晰的查询意图

## 7. `TypedStoreModel`

职责：

- 可选的 Active Record 风格语法糖
- 让简单模型可以直接通过 store 做 CRUD

### 绑定方法

- `set_default_store(store)` — 全局默认 store
- `cls.use_store(store)` — 绑定到特定 model class
- `cls.store()` — 解析当前绑定的 store

### 实例方法

- `insert(*, store=None, session=None, commit=True)` / `ainsert(...)` — 插入自身
- `insert_many(entities, *, ...)` / `ainsert_many(...)` — 批量插入

### 类方法

- `get(ident, *, ...)` / `aget(...)` — 按主键查询
- `find_one(*filters, spec=None, order=None, ...)` / `afind_one(...)` — 查询单条
- `find_many(*filters, spec=None, order=None, limit=None, offset=None, ...)` / `afind_many(...)` — 查询多条
- `paginate(*filters, spec=None, order=None, limit=None, offset=None, ...)` / `apaginate(...)` — 分页
- `update_fields(values, *filters, spec=None, ...)` / `aupdate_fields(...)` — 批量更新字段
- `delete_where(*filters, spec=None, ...)` / `adelete_where(...)` — 条件删除

### 使用示例

```python
from typed_store import TypedStoreModel, set_default_store

set_default_store(store)

class User(Base, TypedStoreModel):
    ...

User(name="alice").insert()
items = User.find_many(User.role == "admin")
```

适用场景：简单模型操作、演示与小型项目

不推荐的场景：复杂 repository 查询编排、跨多个实体的 service 事务协调

## 8. `SessionProvider`

职责：

- 提供 sync / async session scope
- 统一 session 生命周期与异常回滚行为

当前方法：

- `get_session()` — sync session context manager
- `get_async_session()` — async session context manager

## 9. `UnitOfWork` / `AsyncUnitOfWork`

职责：

- 定义显式事务边界
- 让 service 层可以组合多个 repository 操作

当前主要方法：

- context manager / async context manager
- `commit()`
- `rollback()`
- `.session`

## 10. Error surface

当前明确暴露的错误类型：

- `TypedStoreError` — 基类
- `TypedStoreConfigurationError` — 配置错误基类
- `MissingSyncSessionFactoryError` — 缺少 sync session factory
- `MissingAsyncSessionFactoryError` — 缺少 async session factory
- `MissingGlobalStoreError` — TypedStoreModel 未配置默认 store
- `InvalidStoreBindingError` — model store 绑定类型不匹配
- `ProjectionPaginationError` — 投影查询误用 `paginate()`

## 11. Recommended usage by scenario

### Scenario A: simple sync script

优先使用：`SyncTypedStore.from_url()` + 内联 filters

### Scenario B: async web app

优先使用：`AsyncTypedStore.from_url()` + `AsyncUnitOfWork` + repository / service

### Scenario C: sync + async 混合

优先使用：`TypedStore.from_url(url, async_url=...)` + `.async_` 访问异步路径

### Scenario D: 快速原型

优先使用：`TypedStoreModel` mixin + `set_default_store()`

### Scenario E: complex domain logic

优先使用：repository + service + `UnitOfWork` / `AsyncUnitOfWork` + `QuerySpec`

## 12. Related docs

- `README.md`
- `docs/design-spec.md`
- `docs/publishing.md`
- `CHANGELOG.md`
