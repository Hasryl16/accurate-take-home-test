from unittest.mock import MagicMock
from qdrant_store import ensure_collection, delete_by_source, upsert_chunks


def test_ensure_collection_creates_if_not_exists():
    """Harus membuat collection baru jika belum ada."""
    mock_client = MagicMock()
    mock_client.get_collections.return_value.collections = []

    ensure_collection(mock_client, "test_col")

    mock_client.create_collection.assert_called_once()
    call_kwargs = mock_client.create_collection.call_args.kwargs
    assert call_kwargs["collection_name"] == "test_col"


def test_ensure_collection_skips_if_already_exists():
    """Tidak boleh membuat ulang collection yang sudah ada."""
    mock_client = MagicMock()
    existing = MagicMock()
    existing.name = "test_col"
    mock_client.get_collections.return_value.collections = [existing]

    ensure_collection(mock_client, "test_col")

    mock_client.create_collection.assert_not_called()


def test_delete_by_source_calls_client_delete():
    """Harus memanggil client.delete dengan filter source_file yang benar."""
    mock_client = MagicMock()

    delete_by_source(mock_client, "my_col", "modul.pdf")

    mock_client.delete.assert_called_once()
    call_kwargs = mock_client.delete.call_args.kwargs
    assert call_kwargs["collection_name"] == "my_col"


def test_upsert_chunks_builds_correct_points():
    """Points yang di-upsert harus memiliki vector dan payload yang benar."""
    mock_client = MagicMock()
    chunks = [
        {
            "id": "abc-123",
            "page_number": 3,
            "chunk_index": 0,
            "source_file": "modul.pdf",
            "text": "Isi chunk pertama.",
        }
    ]
    embeddings = [[0.1] * 1024]

    upsert_chunks(mock_client, "my_col", chunks, embeddings)

    mock_client.upsert.assert_called_once()
    call_kwargs = mock_client.upsert.call_args.kwargs
    assert call_kwargs["collection_name"] == "my_col"
    points = call_kwargs["points"]
    assert len(points) == 1
    assert points[0].id == "abc-123"
    assert points[0].payload["page_number"] == 3
    assert points[0].payload["text"] == "Isi chunk pertama."
    assert len(points[0].vector) == 1024
