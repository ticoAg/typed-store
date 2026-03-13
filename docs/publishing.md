# Publishing Setup

本文档描述如何为当前仓库的 `TypedStore` 包配置 TestPyPI / PyPI Trusted Publisher，并使用仓库内已有的 workflow 完成发布。

## 1. Current workflow files

仓库中已存在：

- CI: `.github/workflows/ci.yml`
- Release: `.github/workflows/release.yml`

当前发布策略：

- `push` tag `v*`：自动发布到 PyPI
- `workflow_dispatch`：手动选择发布到 `testpypi` 或 `pypi`

## 2. Before remote publishing

在远程发布前，先确认以下内容一致：

- GitHub 仓库 owner / repo 名称
- workflow 文件路径：`.github/workflows/release.yml`
- GitHub environment 名称：`testpypi`、`pypi`
- `pyproject.toml` 中的项目名：`typed-store`
- `pyproject.toml` 中的版本号与准备发布的 tag 一致

## 3. Configure TestPyPI Trusted Publisher

如果 `typed-store` 还没有在 TestPyPI 上存在，推荐使用 pending publisher 方式创建项目。

### 3.1 In TestPyPI

登录 TestPyPI 后：

1. 进入 account publishing 设置
2. 添加 GitHub Actions Trusted Publisher
3. 填写：
   - Owner: `<your-github-owner>`
   - Repository name: `<your-github-repo>`
   - Workflow filename: `release.yml`
   - Environment name: `testpypi`
   - Project name: `typed-store`

如果项目已存在，也可以在项目设置里添加 normal publisher；字段同上，只是不需要“pending project creation”路径。

### 3.2 In GitHub

在仓库中创建 environment：

- `testpypi`

建议：

- 为 `testpypi` environment 增加审批或分支 / tag 限制
- 至少限制只有维护者可以触发真正的 publish job

## 4. Configure PyPI Trusted Publisher

在 PyPI 上重复类似步骤，区别只有：

- Environment name: `pypi`
- 发布目标是正式索引

在 GitHub 中还需要创建：

- `pypi`

## 5. Local verification before publish

在本地建议先执行：

```bash
uv sync --group dev --locked
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
uv build
uv run --with twine twine check dist/*
```

## 6. Manual TestPyPI release

在完成 Trusted Publisher 配置后，可使用：

- GitHub Actions -> `Release` workflow
- `workflow_dispatch`
- 选择 `repository = testpypi`

预期行为：

1. build job 构建 `dist/`
2. publish-testpypi job 获取 OIDC token
3. TestPyPI 接受 Trusted Publisher 身份并完成上传

## 7. PyPI release

推荐流程：

1. 先在 TestPyPI 成功验证一次
2. 确认版本号无误
3. 打 tag：`vX.Y.Z`
4. push tag
5. 由 `release.yml` 自动发布到 PyPI

## 8. Common failure modes

### `invalid-publisher` / `invalid-pending-publisher`

通常表示两边的 identity 不匹配，优先检查：

- GitHub owner
- repository name
- workflow filename (`release.yml`)
- environment name (`testpypi` / `pypi`)

### Project name mismatch

如果使用 pending publisher 创建项目，PyPI / TestPyPI 项目名必须与包元数据中的项目名一致。

当前仓库对应值：

- project name: `typed-store`

## 9. Repo-specific checklist

真正开始远程发布前，请逐项确认：

- [ ] `pyproject.toml` 中 `version` 已更新
- [ ] Git tag 与版本号一致
- [ ] `testpypi` environment 已创建
- [ ] `pypi` environment 已创建
- [ ] TestPyPI Trusted Publisher 已配置
- [ ] PyPI Trusted Publisher 已配置
- [ ] 本地 `ruff` / `ty` / `pytest` / `build` / `twine check` 已通过
- [ ] 先在 TestPyPI 验证过一次
