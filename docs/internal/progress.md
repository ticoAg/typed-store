# TypedStore

- Status: active
- Owner: mixed
- Spec: docs/design-spec.md
- Code SSOT: `typed_store/`, `tests/`, `examples/`, `pyproject.toml`
- Last Updated: 2026-03-29

## Goal

- 在当前工作区把 `TypedStore` 作为类型优先的数据访问 SDK 实现出来
- 用当前仓库作为主实现仓，而不是继续把设计散落在其他项目里

## Current State

- SDK 首版代码已落地，主包位于 `typed_store/`
- public API 已进一步收口为显式 `SyncTypedStore` / `AsyncTypedStore` + `Model.bind(store)`
- `TypedStore` 已降级为 composition root，仅保留 `.sync` / `.async_`
- 已移除默认 store helpers、`TypedStore` sync delegate 与 `store.of()` 模型快捷入口
- examples、README、主路径测试、错误边界测试、smoke 测试和进阶测试已切换到 bind-first 心智模型

## Done

- 建立工作区级 `AGENTS first` 规则体系
- 建立 `docs/internal/workflow.md` 作为恢复与推进真源
- 创建 `docs/design-spec.md` 作为 SDK 设计真源
- 创建本进度文档用于持续追踪
- 新增 `pyproject.toml`，完成项目依赖与测试配置
- 实现 `typed_store/engine.py`
- 实现 `typed_store/session.py`
- 实现 `typed_store/uow.py`
- 实现 `typed_store/query_spec.py`
- 实现 `typed_store/results.py`
- 实现 `typed_store/sync.py`
- 实现 `typed_store/async_store.py`
- 实现 `typed_store/store.py`
- 实现 `typed_store/model.py`
- 移除旧 `compat.py` 兼容层
- 补充 `examples/sync_basic.py`
- 补充 `examples/async_basic.py`
- 补充同步与异步主路径测试
- 补充事务回滚测试
- 补充外部 session 复用测试
- 补充 loader options 回归测试
- 补充错误边界测试
- 补充 repository/transaction 风格示例
- 补充 async repository / service 示例
- 增加 package 发布元数据、`py.typed` 与 `ruff` / `ty` 工具链配置
- 增加 GitHub Actions CI 工作流
- 增加 GitHub Actions release workflow（GitHub Release -> build -> PyPI publish）
- 增加 `.gitignore`
- 重写并增强 `README.md`
- 新增 `CHANGELOG.md`
- 新增 `docs/api-surface.md`
- 运行 `uv run pytest`，当前结果：21 passed
- 运行 `uv run ruff check .` / `uv run ruff format --check .` / `uv run ty check`，当前结果：全部通过
- 运行 `uv build`，确认当前包可生成 sdist 和 wheel
- 新增 `typed_store/bound_model.py`
- 新增 `tests/test_bound_model.py`
- 为 `SyncTypedStore` / `AsyncTypedStore` / `TypedStore` 增加显式生命周期 API
- 将 `TypedStoreModel` 改为 bind-first 纯函数式入口
- 移除全局默认 store helpers 与 `TypedStore` sync delegate
- 移除 `store.of()` 模型快捷入口
- 重写 `examples/model_mixin.py` / `examples/model_store_view.py` 为 bind-first 示例

## Next

- 继续推进 capability protocol 抽象
- 拆分 `QuerySpec` 为更小的 request/spec 对象
- 评估 SQL 级 bulk update/delete 语义
- 配置并验证仓库侧 Trusted Publisher（PyPI / TestPyPI）

## Evidence

- `pyproject.toml`
- `typed_store/__init__.py`
- `typed_store/engine.py`
- `typed_store/session.py`
- `typed_store/uow.py`
- `typed_store/query_spec.py`
- `typed_store/results.py`
- `typed_store/sync.py`
- `typed_store/async_store.py`
- `typed_store/store.py`
- `typed_store/model.py`
- `examples/sync_basic.py`
- `examples/async_basic.py`
- `examples/repository_pattern.py`
- `examples/async_repository_pattern.py`
- `tests/conftest.py`
- `tests/test_sync_store.py`
- `tests/test_async_store.py`
- `tests/test_error_boundaries.py`
- `tests/test_examples.py`
- `.github/workflows/release.yml`
- `docs/publishing.md`
- `docs/api-surface.md`
- `CHANGELOG.md`
- 验证命令：`uv run pytest`
- 验证命令：`uv build`

## Risks / Blockers

- bind-first 主路径已落地，但 capability protocol 与 spec protocol 仍未抽出
- examples 当前仍偏最小演示，若要面向外部使用，还需要补更完整的 repository / transaction 场景示例
- release workflow 依赖 PyPI Trusted Publisher 和 GitHub environment 预配置；未配置前无法真正完成发布
