import os
import tempfile
import pytest

from app.knowledge_engine.loaders import (
    get_loader,
    load_document,
    load_directory
)


# ----------------------------
# get_loader Tests
# ----------------------------

def test_get_loader_file_not_found():
    with pytest.raises(FileNotFoundError):
        get_loader("non_existent.pdf")


def test_get_loader_unsupported_extension(tmp_path):
    # Create temporary .txt file
    file_path = tmp_path / "test.txt"
    file_path.write_text("dummy")

    with pytest.raises(ValueError):
        get_loader(str(file_path))


# ----------------------------
# load_document Tests
# ----------------------------

def test_load_document_invalid_file():
    with pytest.raises(RuntimeError):
        load_document("fake.pdf")


# ----------------------------
# load_directory Tests
# ----------------------------

def test_load_directory_invalid_path():
    with pytest.raises(NotADirectoryError):
        load_directory("not_a_directory")


def test_load_directory_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        docs = load_directory(tmpdir)
        assert docs == []


def test_load_directory_skips_unsupported(tmp_path):
    # Create unsupported file
    file_path = tmp_path / "file.txt"
    file_path.write_text("dummy")

    docs = load_directory(str(tmp_path))
    assert docs == []

from unittest.mock import patch, MagicMock
from langchain_core.documents import Document


# ----------------------------
# Mock load_document success
# ----------------------------

@patch("app.knowledge_engine.loaders.get_loader")
def test_load_document_success(mock_get_loader):
    # Create fake loader
    fake_loader = MagicMock()
    fake_loader.load.return_value = [
        Document(page_content="Test content")
    ]

    mock_get_loader.return_value = fake_loader

    from app.knowledge_engine.loaders import load_document

    docs = load_document("fake.pdf")

    assert len(docs) == 1
    assert docs[0].page_content == "Test content"
