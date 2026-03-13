# API Surface

本文档概述 `TypedStore` 当前对外推荐使用的 API surface，目的是帮助使用者快速判断：

- 应该从哪个入口开始
- 不同对象分别负责什么
- 哪些场景适合 facade，哪些场景适合 mixin 或 repository

## 1. Primary entry points

当前推荐的主要入口有三类：

- `SyncTypedStore`
- `AsyncTypedStore`
- `TypedStore`

其中：

- `SyncTypedStore`：同步代码路径的主入口
- `AsyncTypedStore`：异步代码路径的主入口
- `TypedStore`：bundle，只是同时暴露 `.sync` 和 `.async_`

## 2. `SyncTypedStore`

职责：

- 面向同步 SQLAlchemy session 的 typed facade
- 封装插入、查询、分页、更新、删除等基础行为
- 提供同步 unit of work

当前主要方法：

- `insert(entity, *, session=None, commit=True, refresh=False)`
- `insert_many(entities, *, session=None, commit=True)`
- `get(model, ident, *, session=None)`
- `find_one(model, spec=None, *, session=None)`
- `find_many(model, spec=None, *, session=None)`
- `select_rows(model, spec, *, session=None)`
- `select_scalars(statement, *, session=None)`
- `paginate(model, spec=None, *, session=None)`
- `update_fields(model, values, spec=None, *, session=None, commit=True)`
- `delete_where(model, spec=None, *, session=None, commit=True)`
- `unit_of_work(auto_commit=True)`
- `equals_spec(model, **kwargs)`

适用场景：

- 脚本
- 同步服务层
- repository 层
- 小型工具程序

## 3. `AsyncTypedStore`

职责：

- 面向异步 SQLAlchemy session 的 typed facade
- 在异步路径上提供与同步 facade 尽量对称的 API
- 提供异步 unit of work

当前主要方法：

- `insert(entity, *, session=None, commit=True, refresh=False)`
- `insert_many(entities, *, session=None, commit=True)`
- `get(model, ident, *, session=None)`
- `find_one(model, spec=None, *, session=None)`
- `find_many(model, spec=None, *, session=None)`
- `select_rows(model, spec, *, session=None)`
- `select_scalars(statement, *, session=None)`
- `paginate(model, spec=None, *, session=None)`
- `update_fields(model, values, spec=None, *, session=None, commit=True)`
- `delete_where(model, spec=None, *, session=None, commit=True)`
- `unit_of_work(auto_commit=True)`
- `equals_spec(model, **kwargs)`

适用场景：

- FastAPI / Starlette 等 async 服务
- 异步任务执行器
- 需要 async SQLAlchemy session 的 repository / service 层

## 4. `TypedStore`

职责：

- 作为组合入口组织 sync / async facade

当前公开属性：

- `.sync`
- `.async_`

说明：

- `TypedStore` 自身不承载主要业务方法
- 推荐把它理解为一个 facade bundle，而不是主要执行对象

## 5. `QuerySpec`

职责：

- 把查询意图组织成稳定对象
- 避免在业务代码里散落太多位置参数和 `**kwargs`

当前主要能力：

- `QuerySpec.empty()`
- `.where(*filters)`
- `.order(*clauses)`
- `.paginate(limit=..., offset=...)`
- `.select_columns(*columns)`
- `.with_options(*options)`
- `.build_select(model)`
- `.count_select(model)`

适用场景：

- repository 内构建可复用查询
- 在 service 层表达清晰的查询意图
- 组合筛选、排序、分页与 loader options

## 6. `TypedStoreModel`

职责：

- 提供可选模型语法糖
- 让简单模型可以直接通过 store 做 CRUD

当前主要方法：

- `insert()` / `ainsert()`
- `get()` / `aget()`
- `find_one()` / `afind_one()`
- `find_many()` / `afind_many()`
- `paginate()` / `apaginate()`
- `delete_where()` / `adelete_where()`
- `use_store(store)`
- `store()`

适用场景：

- 简单模型操作
- 演示与小型项目
- 需要最小心智负担的 CRUD 场景

不推荐的场景：

- 复杂 repository 查询编排
- 跨多个实体的 service 事务协调
- 需要严格限制模型层职责的项目

## 7. `SessionProvider`

职责：

- 提供 sync / async session scope
- 统一 session 生命周期与异常回滚行为

当前方法：

- `get_session()`
- `get_async_session()`

通常配合：

- `SyncTypedStore`
- `AsyncTypedStore`
- `UnitOfWork`
- `AsyncUnitOfWork`

## 8. `UnitOfWork` / `AsyncUnitOfWork`

职责：

- 定义显式事务边界
- 让 service 层可以组合多个 repository 操作

当前主要方法：

- context manager / async context manager
- `commit()`
- `rollback()`
- `.session`

推荐用法：

- 在 service 层围绕一个业务动作开启事务
- 把 repository 操作都统一放在同一个 session 上执行

## 9. Error surface

当前明确暴露的错误类型包括：

- `TypedStoreError`
- `TypedStoreConfigurationError`
- `MissingSyncSessionFactoryError`
- `MissingAsyncSessionFactoryError`
- `MissingGlobalStoreError`
- `InvalidStoreBindingError`
- `ProjectionPaginationError`

这些异常主要覆盖：

- session factory 缺失
- model store 绑定错误
- 将 projection query 错误传给 `paginate()`

## 10. Recommended usage by scenario

### Scenario A: simple sync script

优先使用：

- `SyncTypedStore`
- `QuerySpec`

### Scenario B: async web app

优先使用：

- `AsyncTypedStore`
- `SessionProvider`
- `AsyncUnitOfWork`
- repository + service

### Scenario C: complex domain logic

优先使用：

- repository + service
- `UnitOfWork` / `AsyncUnitOfWork`
- `QuerySpec`

不建议把复杂逻辑堆进 `TypedStoreModel`

## 11. Non-primary surfaces

以下内容存在，但不应被视为主公共设计卖点：

- `TypedStore` 作为 bundle 的轻量转发能力
- `TypedStoreModel` 的全局默认 store 绑定
- `QuerySpec.build_select()` / `count_select()` 这种更靠近底层的 helper

## 12. Related docs

- `README.md`
- `docs/specs/typed-store.md`
- `docs/architecture/publishing.md`
- `CHANGELOG.md`
