# TypedStore

`TypedStore` 是一个构建在 SQLAlchemy 2.x 之上的类型优先数据访问 SDK。

它不尝试替代 SQLAlchemy，也不重新发明 ORM；它的目标是把项目里重复出现的数据访问模式收敛成一组更稳定、更清晰、更适合类型检查的 facade，包括：

- 显式分离的 sync / async store
- 基于 `QuerySpec` 的查询意图建模
- 明确的 `UnitOfWork` 事务边界
- 可选的 `TypedStoreModel` 语法糖
- 默认集成 `ruff` + `ty` + `pytest` 的开发链路

## Status

当前状态：`Alpha`

这意味着：

- 核心 API 已经可用
- sync / async 主路径、边界测试、examples smoke 已覆盖
- 仍然可能继续收敛 API 表面和类型表达
- 在正式公开发布前，建议先通过 TestPyPI 做一轮验证

## Why TypedStore

如果你已经直接使用 SQLAlchemy，`TypedStore` 想解决的问题不是“让你不用 SQLAlchemy”，而是：

- 避免每个项目自己重复写 session scope、CRUD facade、分页与事务样板代码
- 在 sync / async 两条路径上给出更一致的行为语义
- 用 `QuerySpec` 把查询条件、排序、分页、投影和 loader options 收拢到一个稳定对象里
- 在保持 SQLAlchemy escape hatch 的前提下，减少散落的 `dict` / `Any` 风格数据访问代码

换句话说，`TypedStore` 更像：

- a typed data access layer
- a repository-friendly SDK
- a light, explicit facade over SQLAlchemy

而不是：

- a new ORM
- a schema migration tool
- a full Active Record framework

## Design Principles

- `Type-first`：优先考虑静态可推断性，而不是“一个万能方法包打天下”
- `SQLAlchemy-native`：保留 SQLAlchemy 作为底层单一事实来源
- `Explicit sync/async`：同步与异步 API 分离，而不是把双重语义塞进同一个主类
- `Small surface`：只收敛证明有价值的共性，不做过度抽象
- `Code as SSOT`：代码和测试是行为真源，文档负责解释边界、意图和流程

## Feature Matrix

| Capability | Status | Notes |
|---|---|---|
| `SyncTypedStore` | done | 同步 facade |
| `AsyncTypedStore` | done | 异步 facade |
| `TypedStore` bundle | done | 暴露 `.sync` / `.async_` |
| `QuerySpec` | done | 过滤、排序、分页、投影、loader options |
| `UnitOfWork` / `AsyncUnitOfWork` | done | 事务边界 |
| `TypedStoreModel` | done | 可选语法糖 |
| examples | done | sync / async / repository / async repository |
| examples smoke tests | done | `tests/test_examples.py` |
| `ruff` + `ty` + `pytest` | done | 默认开发检查链路 |
| GitHub CI | done | `.github/workflows/ci.yml` |
| GitHub release workflow | done | `.github/workflows/release.yml` |
| PyPI/TestPyPI Trusted Publisher config | pending | 需在远程平台侧完成 |

## Compatibility

- Python: `>=3.13`
- SQLAlchemy: `>=2.0.36`
- Tested locally with:
  - Python `3.13`
  - SQLAlchemy `2.0.48`

## Project Layout

```text
./
├── typed_store/
├── tests/
├── examples/
├── docs/
│   ├── architecture/
│   └── specs/
├── .github/workflows/
├── pyproject.toml
└── README.md
```

## Read Order

如果你第一次进入仓库，推荐阅读顺序：

1. `AGENTS.md`
2. `workflow.md`
3. `README.md`
4. `docs/architecture/api-surface.md`
5. `docs/specs/typed-store.md`
6. `todo/typed-store.md`

## Installation

本地开发：

```bash
uv sync --group dev
```

安装包到当前环境：

```bash
uv pip install -e .
```

构建分发包：

```bash
uv build
```

## Public API

当前 public API 以显式 sync / async facade 为主：

- `SyncTypedStore`
- `AsyncTypedStore`
- `TypedStore`
- `QuerySpec`
- `TypedStoreModel`
- `SessionProvider`
- `UnitOfWork`
- `AsyncUnitOfWork`

更完整的 API 说明见：`docs/architecture/api-surface.md`

## Quick Start

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

### Model mixin

```python
from typed_store import TypedStoreModel, set_default_store

set_default_store(typed_store)

class User(Base, TypedStoreModel):
    ...

User(name="alice").insert()
items = User.find_many()
```

### Repository style

```python
repo = UserRepository(store.sync)
service = UserService(store.sync)
service.register_admin("alice@example.com")
```

## Examples

完整示例见：

- `examples/sync_basic.py`
- `examples/async_basic.py`
- `examples/repository_pattern.py`
- `examples/async_repository_pattern.py`

示例 smoke 测试见：`tests/test_examples.py`

## Design Trade-offs

### Why keep `TypedStoreModel`

`TypedStoreModel` 不是主入口，而是可选语法糖。

保留它的原因：

- 对简单模型 CRUD 很顺手
- 能作为小型项目的轻量入口

限制它的原因：

- 不希望模型承担复杂查询编排
- 不希望模型自行掌握事务边界
- 更推荐复杂业务使用 repository + service + unit of work

### Why `TypedStore` is only a bundle

`TypedStore` 本身只暴露：

- `.sync`
- `.async_`

这样做是为了避免一个类同时承担 sync / async 双重语义，让 public API 更清晰。

## Typing Limitations

当前类型系统已经比较收敛，但仍有几个已知现实边界：

- SQLAlchemy 的可变长列投影 `select(*columns)` 在静态分析上并不总是完全精确，因此 `QuerySpec.select_columns()` 附近保留了最小必要的工具链兼容处理
- `TypedStoreModel` 同时要满足运行时错误绑定保护和静态类型约束，因此内部仍存在少量 `cast`
- `select_rows()` 的返回值仍然偏宽，因为 row shape 取决于调用方提供的投影列

这些限制并不是设计失控，而是 SQLAlchemy typing 边界与可维护性之间的权衡。

## Verification

当前最低验证命令：

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv build
uv run --with twine twine check dist/*
```

## CI

GitHub Actions workflow: `.github/workflows/ci.yml`

默认检查链路：

```bash
uv sync --group dev --locked
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
```

## Release Automation

GitHub Release workflow: `.github/workflows/release.yml`

发布链路：

1. `push` tag `v*`：自动构建并发布到 PyPI
2. `workflow_dispatch`：可手动选择发布到 `testpypi` 或 `pypi`
3. workflow 会先构建分发包，再通过 Trusted Publisher 发布

发布前提：

- 需要在 PyPI / TestPyPI 上为本仓库配置 Trusted Publisher
- GitHub 仓库需要存在环境：`pypi`、`testpypi`
- 建议 release tag 与 `pyproject.toml` 中的 `version` 保持一致
- 该流程已在仓库中落地，但尚未在本地触发真实远程发布

发布配置清单见：`docs/architecture/publishing.md`

## Changelog

版本变更记录见：`CHANGELOG.md`
