import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def chunk_pages(
    pages: list[dict],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[dict]:

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
