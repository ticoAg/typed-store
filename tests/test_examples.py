from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_example(script_name: str, tmp_path: Path) -> str:
    env = os.environ.copy()
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "examples" / script_name)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def test_sync_basic_example_smoke(tmp_path: Path) -> None:
    output = run_example("sync_basic.py", tmp_path)
    assert "alice" in output


def test_async_basic_example_smoke(tmp_path: Path) -> None:
    output = run_example("async_basic.py", tmp_path)
    assert "alice" in output


def test_repository_pattern_example_smoke(tmp_path: Path) -> None:
    output = run_example("repository_pattern.py", tmp_path)
    assert "alice@example.com" in output


def test_async_repository_pattern_example_smoke(tmp_path: Path) -> None:
    output = run_example("async_repository_pattern.py", tmp_path)
    assert "alice@example.com" in output


def test_model_store_view_example_smoke(tmp_path: Path) -> None:
    output = run_example("model_store_view.py", tmp_path)
    assert "alice" in output
    assert "members:" in output


def test_model_mixin_example_smoke(tmp_path: Path) -> None:
    output = run_example("model_mixin.py", tmp_path)
    assert "admins:" in output
    assert "find_one:" in output
    assert "updated" in output
    assert "deleted" in output


def test_readme_teaches_query_and_bind_first() -> None:
    readme = (REPO_ROOT / "README.md").read_text()

    assert "User.bind(store)" in readme
    assert "Query[" in readme
    assert "PageRequest(" in readme
    assert "QuerySpec" not in readme


def test_examples_no_longer_use_queryspec() -> None:
    sync_example = (REPO_ROOT / "examples" / "sync_basic.py").read_text()
    async_example = (REPO_ROOT / "examples" / "async_basic.py").read_text()

    assert "Query[" in sync_example
    assert "QuerySpec" not in sync_example
    assert "Query[" in async_example
    assert "QuerySpec" not in async_example
