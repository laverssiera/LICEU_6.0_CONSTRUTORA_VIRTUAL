from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from fastapi import APIRouter
import uuid
import time

router = APIRouter()

model = SentenceTransformer("all-MiniLM-L6-v2")

qdrant = QdrantClient(
    host="localhost",
    port=6333
)

COLLECTION = "liceu_collective_memory"

try:
    qdrant.get_collection(COLLECTION)
except:
    qdrant.recreate_collection(
        collection_name=COLLECTION,
        vectors_config={
            "size": 384,
            "distance": "Cosine"
        }
    )

class CollectiveMemory:

    @staticmethod
    def store(text, metadata):
        vector = model.encode(text).tolist()

        qdrant.upsert(
            collection_name=COLLECTION,
            points=[{
                "id": str(uuid.uuid4()),
                "vector": vector,
                "payload": {
                    "text": text,
                    "metadata": metadata,
                    "timestamp": time.time()
                }
            }]
        )

    @staticmethod
    def search(query):
        vector = model.encode(query).tolist()

        return qdrant.search(
            collection_name=COLLECTION,
            query_vector=vector,
            limit=5
        )

@router.post("/runtime/cognition/store")
async def store(payload: dict):
    CollectiveMemory.store(
        payload["text"],
        payload.get("metadata", {})
    )

    return {
        "status": "stored"
    }

@router.get("/runtime/cognition/search")
async def search(query: str):
    results = CollectiveMemory.search(query)

    return {
        "results": [r.payload for r in results],
        "runtime_identity": "Distributed Collective Cognition Runtime"
    }