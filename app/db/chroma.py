import chromadb

from app.core.config import CHROMA_JOBS_COLLECTION, CHROMA_PERSIST_DIR

chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

jobs_collection = chroma_client.get_or_create_collection(name=CHROMA_JOBS_COLLECTION)
