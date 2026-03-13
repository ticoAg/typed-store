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
