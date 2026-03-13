# TypedStore

[![Python](https://img.shields.io/badge/python-%E2%89%A53.13-blue)](https://www.python.org/) [![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-%E2%89%A52.0.36-green)](https://www.sqlalchemy.org/) [![License: MIT](https://img.shields.io/badge/license-MIT-yellow)](LICENSE) [![Status](https://img.shields.io/badge/status-alpha-orange)]()

Type-first data access SDK built on top of SQLAlchemy 2.x.

TypedStore 把项目中重复出现的 session 管理、CRUD facade、分页与事务样板收敛为一组类型安全的 API——不替代 SQLAlchemy，只做它上层的薄 facade。

## Features

- **Explicit sync / async** — `SyncTypedStore` 与 `AsyncTypedStore` 分离，无隐式双重语义
- **QuerySpec** — 过滤、排序、分页、投影、loader options 统一建模
- **UnitOfWork** — 明确的事务边界（sync / async）
- **TypedStoreModel** — 可选的 Active Record 风格语法糖
- **TypedStore bundle** — 通过 `.sync` / `.async_` 一站式访问

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
from typed_store import EngineConfig, QuerySpec, SessionProvider, SyncTypedStore, build_engine_bundle

bundle = build_engine_bundle(sync_config=EngineConfig(url="sqlite:///app.sqlite3"))
provider = SessionProvider(sync_session_factory=bundle.sync_session_factory)
store = SyncTypedStore(provider)

rows = store.find_many(User, QuerySpec[User].empty().where(User.email == "alice@example.com"))
```

### Async

```python
from typed_store import AsyncTypedStore, EngineConfig, QuerySpec, SessionProvider, build_engine_bundle

bundle = build_engine_bundle(async_config=EngineConfig(url="sqlite+aiosqlite:///app.sqlite3"))
provider = SessionProvider(async_session_factory=bundle.async_session_factory)
store = AsyncTypedStore(provider)

rows = await store.find_many(User, QuerySpec[User].empty().where(User.email == "alice@example.com"))
```

### Model Mixin

```python
from typed_store import TypedStoreModel, set_default_store

set_default_store(typed_store)

class User(Base, TypedStoreModel):
    ...

User(name="alice").insert()
items = User.find_many()
```

### Repository Pattern

```python
repo = UserRepository(store.sync)
service = UserService(store.sync)
service.register_admin("alice@example.com")
```

> 完整示例见 [`examples/`](examples/)，对应 smoke 测试见 [`tests/test_examples.py`](tests/test_examples.py)。

## Requirements

| Dependency | Version   |
| ---------- | --------- |
| Python     | >= 3.13   |
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
