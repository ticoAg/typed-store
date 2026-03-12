# Workspace Repo

这是当前工作目录的研发工作区仓库，也是 `TypedStore` SDK 的主实现仓。

它的目标不是先定义某个具体业务产品，而是先建立一套可持续演进的协作与研发底座，使后续在这里落地的模块、实验、工具或子项目都能遵循统一的工作方式：

- `AGENTS first`
- `Code as SSOT`
- `Progress is traceable`

当前首个实现主题是 `TypedStore`：一个构建在 SQLAlchemy 之上的类型优先数据访问 SDK。

## Read Order

进入仓库后，推荐阅读顺序：

1. `AGENTS.md`
2. `workflow.md`
3. `docs/README.md`
4. `todo/README.md`
5. `docs/specs/typed-store.md`
6. `todo/typed-store.md`

## Workspace Layout

```text
./
├── AGENTS.md
├── workflow.md
├── README.md
├── pyproject.toml
├── typed_store/
├── tests/
├── examples/
├── docs/
│   ├── README.md
│   ├── architecture/
│   └── specs/
├── todo/
└── .agent/
    └── rules/
```

## Core Rules

- 工作区级长期规则以 `AGENTS.md` 为准
- 工作流、恢复路径、交接方式以 `workflow.md` 为准
- 代码和测试是行为真源
- 文档负责解释结构、意图、边界和进度，不复制代码
- 每个持续推进的主题都应在 `todo/` 中可被追踪

## Current Topic

- 设计真源：`docs/specs/typed-store.md`
- 进度追踪：`todo/typed-store.md`
- 代码真源：`typed_store/`
- 测试真源：`tests/`

## Public API

当前 public API 以显式 sync / async facade 为主：

- `SyncTypedStore`
- `AsyncTypedStore`
- `TypedStore`（仅作为组合入口，暴露 `.sync` 与 `.async_`）
- `QuerySpec`
- `TypedStoreModel`
- `SessionProvider`
- `UnitOfWork` / `AsyncUnitOfWork`

不再维护旧 `DBORM` 风格兼容层。

## Usage

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

完整示例见：

- `examples/sync_basic.py`
- `examples/async_basic.py`
- `examples/repository_pattern.py`
- `examples/async_repository_pattern.py`

示例 smoke 测试见：`tests/test_examples.py`

## Verification

当前最低验证命令：

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv build
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

1. 在 GitHub 创建一个 `published` 状态的 Release
2. workflow 会先重新执行默认检查链路
3. 通过后运行 `uv build` 生成 sdist 和 wheel
4. 使用 Trusted Publishing 发布到 PyPI

发布前提：

- 需要在 PyPI 上为本仓库配置 Trusted Publisher
- GitHub 仓库需要存在环境：`pypi`
- 建议 release tag 与 `pyproject.toml` 中的 `version` 保持一致
- 该流程已在仓库中落地，但尚未在本地触发真实远程发布


发布配置清单见：`docs/architecture/publishing.md`
