from sentence_transformers import SentenceTransformer

from app.core.config import EMBEDDING_MODEL_NAME

_model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_text(text: str) -> list[float]:
    return _model.encode(text).tolist()
