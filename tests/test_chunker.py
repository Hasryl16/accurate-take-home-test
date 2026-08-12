from chunker import chunk_pages


def test_chunk_preserves_page_number():
    """Setiap chunk harus membawa page_number dari halamannya."""
    pages = [
        {"page_number": 7, "text": "kata " * 300, "source_file": "modul.pdf"}
    ]
    chunks = chunk_pages(pages)
    assert all(c["page_number"] == 7 for c in chunks)


def test_short_text_stays_single_chunk():
    """Teks pendek tidak boleh dipecah."""
    pages = [
        {"page_number": 1, "text": "Teks singkat.", "source_file": "modul.pdf"}
    ]
    chunks = chunk_pages(pages)
    assert len(chunks) == 1
    assert chunks[0]["text"] == "Teks singkat."


def test_long_text_splits_into_multiple_chunks():
    """Teks panjang harus dipecah menjadi beberapa chunk."""
    long_text = "a" * 3000
    pages = [
        {"page_number": 2, "text": long_text, "source_file": "modul.pdf"}
    ]
    chunks = chunk_pages(pages)
    assert len(chunks) > 1


def test_chunk_has_all_required_metadata_fields():
    """Setiap chunk harus punya id, page_number, chunk_index, source_file, text."""
    pages = [
        {"page_number": 5, "text": "Konten halaman lima.", "source_file": "modul.pdf"}
    ]
    chunks = chunk_pages(pages)
    required_fields = {"id", "page_number", "chunk_index", "source_file", "text"}
    for chunk in chunks:
        assert required_fields.issubset(chunk.keys()), f"Missing fields in: {chunk.keys()}"


def test_chunk_index_is_sequential_per_page():
    """chunk_index harus mulai dari 0 dan naik urut per halaman."""
    long_text = "kata panjang " * 200
    pages = [
        {"page_number": 3, "text": long_text, "source_file": "modul.pdf"}
    ]
    chunks = chunk_pages(pages)
    indices = [c["chunk_index"] for c in chunks]
    assert indices == list(range(len(chunks)))


def test_multiple_pages_each_get_correct_page_number():
    """Chunk dari halaman berbeda tidak boleh tercampur page_number-nya."""
    pages = [
        {"page_number": 10, "text": "Halaman sepuluh. " * 50, "source_file": "modul.pdf"},
        {"page_number": 20, "text": "Halaman dua puluh. " * 50, "source_file": "modul.pdf"},
    ]
    chunks = chunk_pages(pages)
    page_10_chunks = [c for c in chunks if c["page_number"] == 10]
    page_20_chunks = [c for c in chunks if c["page_number"] == 20]
    assert len(page_10_chunks) > 0
    assert len(page_20_chunks) > 0
    assert len(page_10_chunks) + len(page_20_chunks) == len(chunks)
