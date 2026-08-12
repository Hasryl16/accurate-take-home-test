import os
import cohere
from dotenv import load_dotenv

from extract import extract_pages
from chunker import chunk_pages
from qdrant_store import get_client, ensure_collection, delete_by_source, upsert_chunks

load_dotenv()

PDF_PATH = "docs/MODUL PEMBELAJARAN.pdf"
BATCH_SIZE = 90  # Cohere API limit: 96 per request, use 90 to be safe


def embed_chunks(chunks: list[dict]) -> list[list[float]]:
    """Generate embeddings untuk semua chunks via Cohere, dalam batch."""
    co = cohere.ClientV2(os.getenv("COHERE_API_KEY"))
    texts = [c["text"] for c in chunks]
    embeddings = []

    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
    for batch_num, i in enumerate(range(0, len(texts), BATCH_SIZE), start=1):
        batch = texts[i : i + BATCH_SIZE]
        resp = co.embed(
            texts=batch,
            model="embed-multilingual-v3.0",
            input_type="search_document",
            embedding_types=["float"],
        )
        embeddings.extend(resp.embeddings.float_)
        print(f"  Batch {batch_num}/{total_batches}: {len(batch)} chunks embedded")

    return embeddings


def main() -> None:
    print("=" * 40)
    print("  Accenture RAG — Ingestion Pipeline")
    print("=" * 40)

    # 1. Ekstrak teks per halaman
    print(f"\n[1/4] Extracting pages dari {PDF_PATH} ...")
    pages = extract_pages(PDF_PATH)
    print(f"  → {len(pages)} halaman dengan konten teks")

    # 2. Chunk per halaman
    print("\n[2/4] Chunking ...")
    chunks = chunk_pages(pages)
    print(f"  → {len(chunks)} chunks total")

    # 3. Generate embeddings
    print("\n[3/4] Generating embeddings (Cohere embed-multilingual-v3.0) ...")
    embeddings = embed_chunks(chunks)
    print(f"  → {len(embeddings)} embeddings generated")

    # 4. Upsert ke Qdrant
    collection = os.getenv("QDRANT_COLLECTION", "accurate_online_docs")
    print(f"\n[4/4] Upserting ke Qdrant collection '{collection}' ...")
    client = get_client()
    ensure_collection(client, collection)

    source_file = os.path.basename(PDF_PATH)
    delete_by_source(client, collection, source_file)
    upsert_chunks(client, collection, chunks, embeddings)
    print(f"  → {len(chunks)} points berhasil di-upsert")

    print("\n✓ Ingestion selesai!")


if __name__ == "__main__":
    main()
