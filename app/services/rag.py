from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.core.config import settings
import uuid

model = SentenceTransformer(settings.EMBEDDING_MODEL)

client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)


def init_collection():
    existing = [c.name for c in client.get_collections().collections]
    if settings.QDRANT_COLLECTION not in existing:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print(f"Collection '{settings.QDRANT_COLLECTION}' created.")
    else:
        print(f"Collection '{settings.QDRANT_COLLECTION}' already exists.")


def embed_documents(docs: list[dict]):
    """
    docs = [{"text": "...", "metadata": {...}}, ...]
    """
    init_collection()
    points = []
    for doc in docs:
        vector = model.encode(doc["text"]).tolist()
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={"text": doc["text"], **doc.get("metadata", {})}
        ))
    client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)
    print(f"Embedded {len(points)} documents.")


def search(query: str, top_k: int = 3) -> list[dict]:
    vector = model.encode(query).tolist()
    results = client.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=vector,
        limit=top_k
    )
    return [{"text": r.payload["text"], "score": r.score} for r in results]