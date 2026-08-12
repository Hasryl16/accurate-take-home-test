import os
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

VECTOR_SIZE = 1024  # dimensi Cohere embed-multilingual-v3.0


def get_client() -> QdrantClient:
    """Buat Qdrant client dari environment variables."""
    return QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY") or None,
    )


def ensure_collection(client: QdrantClient, collection: str) -> None:
    """Buat collection jika belum ada. Skip jika sudah ada."""
    existing_names = [c.name for c in client.get_collections().collections]
    if collection not in existing_names:
        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        print(f"  Collection '{collection}' dibuat.")
    else:
        print(f"  Collection '{collection}' sudah ada.")


def delete_by_source(client: QdrantClient, collection: str, source_file: str) -> None:
    """Hapus semua points dengan source_file tertentu (untuk idempotency)."""
    client.delete(
        collection_name=collection,
        points_selector=Filter(
            must=[FieldCondition(key="source_file", match=MatchValue(value=source_file))]
        ),
    )
    print(f"  Deleted existing points for '{source_file}'")


def upsert_chunks(
    client: QdrantClient,
    collection: str,
    chunks: list[dict],
    embeddings: list[list[float]],
) -> None:
    """Upsert chunks beserta embedding-nya ke Qdrant."""
    points = [
        PointStruct(
            id=chunks[i]["id"],
            vector=embeddings[i],
            payload={
                "page_number": chunks[i]["page_number"],
                "chunk_index": chunks[i]["chunk_index"],
                "source_file": chunks[i]["source_file"],
                "text": chunks[i]["text"],
            },
        )
        for i in range(len(chunks))
    ]
    client.upsert(collection_name=collection, points=points)
