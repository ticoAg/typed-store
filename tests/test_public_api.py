from __future__ import annotations

from pathlib import Path

import typed_store

REPO_ROOT = Path(__file__).resolve().parent.parent
LEGACY_QUERY_OBJECT = "Query" + "Spec"
LEGACY_MODEL_STORE_NAMES = ("SyncModel" + "Store", "AsyncModel" + "Store")
LEGACY_DEFAULT_STORE = "set_default_" + "store"


def test_public_exports_include_v1_surface() -> None:
    expected = [
        "SyncTypedStore",
        "AsyncTypedStore",
        "TypedStore",
        "TypedStoreModel",
        "SyncBoundModelView",
        "AsyncBoundModelView",
        "Query",
        "PageRequest",
        "Patch",
        "ProjectionQuery",
        "Page",
        "UnitOfWork",
        "AsyncUnitOfWork",
        "SessionProvider",
        "BulkPatchableStoreProtocol",
        "BulkDeletableStoreProtocol",
        "AsyncBulkPatchableStoreProtocol",
        "AsyncBulkDeletableStoreProtocol",
        "BulkQueryShapeError",
    ]

    for name in expected:
        assert hasattr(typed_store, name), name


def test_public_exports_exclude_removed_surfaces() -> None:
    assert not hasattr(typed_store, LEGACY_QUERY_OBJECT)
    for name in LEGACY_MODEL_STORE_NAMES:
        assert not hasattr(typed_store, name)
    assert not hasattr(typed_store, LEGACY_DEFAULT_STORE)


def test_py_typed_marker_exists() -> None:
    assert (REPO_ROOT / "typed_store" / "py.typed").exists()


def test_release_workflow_supports_manual_and_release_paths() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "release.yml").read_text()

    assert "workflow_dispatch" in workflow
    assert "publish-to-testpypi" in workflow
    assert "publish-to-pypi" in workflow
