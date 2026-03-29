# TypedStore

[![Python](https://img.shields.io/badge/python-%E2%89%A53.12-blue)](https://www.python.org/) [![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-%E2%89%A52.0.36-green)](https://www.sqlalchemy.org/) [![License: MIT](https://img.shields.io/badge/license-MIT-yellow)](LICENSE) [![Status](https://img.shields.io/badge/status-alpha-orange)]()

Type-first data access SDK built on top of SQLAlchemy 2.x.

TypedStore 把项目中重复出现的 session 管理、CRUD facade、分页与事务样板收敛为一组类型安全的 API——不替代 SQLAlchemy，只做它上层的薄 facade。

## Features

- **Explicit sync / async** — `SyncTypedStore` 与 `AsyncTypedStore` 分离，无隐式双重语义
- **One-line init** — `SyncTypedStore.from_url("sqlite:///app.db")` 即可开始使用
- **Protocol-first queries** — `store.find_many(User, query=Query[User]().where(...))`
- **Bind-first models** — `User.bind(store).find_many()` 让模型天然具备显式绑定能力
- **Explicit request objects** — `Query`, `PageRequest`, `Patch`, `ProjectionQuery`
- **UnitOfWork** — 明确的事务边界（sync / async）
- **TypedStoreModel** — 为模型提供纯函数式 `bind(store)` 入口
- **TypedStore composition root** — 通过 `.sync` / `.async_` 统一装配 sync / async store

## Quick Start

### Installation

```bash
pip install typed-store
```

<details>
<summary>本地开发</summary>

```bash
uv sync --group dev
```

</details>

### Sync

```python
from typed_store import PageRequest, Query, SyncTypedStore

store = SyncTypedStore.from_url("sqlite:///app.db")
Base.metadata.create_all(store.engine)

store.insert(User(name="alice"))
query = Query[User]().where(User.role == "admin").order(User.id.asc())
page = PageRequest(limit=10, offset=0)

store.find_many(User, query=query)
store.paginate(User, query=query, page=page)
```

### Async

```python
from typed_store import AsyncTypedStore, PageRequest, Query

store = AsyncTypedStore.from_url("sqlite+aiosqlite:///app.db")

await store.insert(User(name="alice"))
query = Query[User]().where(User.role == "admin")
await store.find_many(User, query=query)
await store.paginate(User, query=query, page=PageRequest(limit=10, offset=0))
```

### TypedStore (sync + async)

```python
from typed_store import Query, TypedStore

ts = TypedStore.from_url("sqlite:///app.db", async_url="sqlite+aiosqlite:///app.db")

# 显式使用 sync store
ts.sync.find_many(User, query=Query[User]())
ts.sync.insert(User(name="alice"))

# 异步明确走 .async_
await ts.async_.find_many(User, query=Query[User]())
```

### Model Binding

```python
from typed_store import PageRequest, Query, SyncTypedStore, TypedStoreModel

store = SyncTypedStore.from_url("sqlite:///app.db")

class User(Base, TypedStoreModel):
    ...

users = User.bind(store)
users.insert(User(name="alice"))
users.find_many(query=Query[User]().where(User.role == "admin"))
users.get(1)
users.paginate(query=Query[User](), page=PageRequest(limit=10, offset=0))
```

### Request Objects

```python
from typed_store import PageRequest, Patch, Query

query = Query[User]().where(User.role == "admin").order(User.id.asc())
page = PageRequest(limit=10, offset=0)
patch = Patch[User]({"role": "superadmin"})

store.find_many(User, query=query)
store.paginate(User, query=query, page=page)
store.update(User, query=Query[User]().where(User.name == "alice"), patch=patch)
```

### Model Mixin

```python
from typed_store import Query, SyncTypedStore, TypedStoreModel

store = SyncTypedStore.from_url("sqlite:///app.db")

class User(Base, TypedStoreModel):
    ...

users = User.bind(store)
users.insert(User(name="alice"))
items = users.find_many(query=Query[User]())
```

### Repository Pattern

```python
store = SyncTypedStore.from_url("sqlite:///app.db")
repo = UserRepository(store)
service = UserService(store)
service.register_admin("alice@example.com")
```

> 完整示例见 [`examples/`](examples/)，对应 smoke 测试见 [`tests/test_examples.py`](tests/test_examples.py)。

## Requirements

| Dependency | Version   |
| ---------- | --------- |
| Python     | >= 3.12   |
| SQLAlchemy | >= 2.0.36 |

## Documentation

| Document                                     | Description   |
| -------------------------------------------- | ------------- |
| [`docs/api-surface.md`](docs/api-surface.md) | 完整 API 说明 |
| [`docs/design-spec.md`](docs/design-spec.md) | 设计规格      |
| [`docs/publishing.md`](docs/publishing.md)   | 发布配置清单  |
| [`CHANGELOG.md`](CHANGELOG.md)               | 版本变更记录  |

## Development

```bash
uv run pytest              # tests
uv run ruff check .        # lint
uv run ruff format --check .  # format check
uv run ty check            # type check
```

## License

[MIT](LICENSE)
