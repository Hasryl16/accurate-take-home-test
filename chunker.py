import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def chunk_pages(
    pages: list[dict],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[dict]:
    """
    Chunk setiap halaman secara terpisah, mempertahankan page_number di metadata.

    Args:
        pages: output dari extract.extract_pages() —
               list of {page_number, text, source_file}
        chunk_size: maksimum karakter per chunk (default 800)
        chunk_overlap: jumlah karakter overlap antar chunk (default 100)

    Returns:
        list of {id, page_number, chunk_index, source_file, text}
    """
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", " ", ""],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = []
    for page in pages:
        page_chunks = splitter.split_text(page["text"])
        for i, chunk_text in enumerate(page_chunks):
            chunks.append({
                "id": str(uuid.uuid4()),
                "page_number": page["page_number"],
                "chunk_index": i,
                "source_file": page["source_file"],
                "text": chunk_text,
            })

    return chunks
