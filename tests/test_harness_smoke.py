"""Harness smoke: shared package is importable after install."""

import sageo


def test_sageo_package_importable() -> None:
    assert sageo.__version__
