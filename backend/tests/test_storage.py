import pytest

from app.services.storage import LocalStorageProvider


@pytest.fixture
def storage(tmp_path):
    return LocalStorageProvider(base_dir=str(tmp_path / "uploads"))


def test_upload_then_download_round_trip(storage):
    name = storage.upload_file(b"policy text", "handbook.txt", "text/plain")

    assert name == "handbook.txt"
    assert storage.download_file(name) == b"policy text"


def test_upload_strips_directory_components(storage, tmp_path):
    name = storage.upload_file(b"x", "../../outside.txt", "text/plain")

    assert name == "outside.txt"
    assert (tmp_path / "uploads" / "outside.txt").exists()
    assert not (tmp_path / "outside.txt").exists()


def test_download_cannot_escape_the_upload_directory(storage, tmp_path):
    (tmp_path / "secret.txt").write_bytes(b"secret")

    with pytest.raises(FileNotFoundError):
        storage.download_file("../secret.txt")


def test_download_missing_file_raises(storage):
    with pytest.raises(FileNotFoundError, match="missing.pdf"):
        storage.download_file("missing.pdf")


def test_delete_reports_whether_a_file_was_removed(storage):
    storage.upload_file(b"x", "a.txt", "text/plain")

    assert storage.delete_file("a.txt") is True
    assert storage.delete_file("a.txt") is False
    with pytest.raises(FileNotFoundError):
        storage.download_file("a.txt")
