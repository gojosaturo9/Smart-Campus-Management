from __future__ import annotations

from functools import lru_cache

from app.core.ats.config import (
    SENTENCE_TRANSFORMER_MODEL,
    SPACY_MODEL_PRIMARY,
    SPACY_MODEL_SECONDARY,
)


@lru_cache(maxsize=1)
def get_ats_models():
    import spacy
    from sentence_transformers import SentenceTransformer

    try:
        nlp = spacy.load(SPACY_MODEL_PRIMARY)
    except OSError:
        try:
            nlp = spacy.load(SPACY_MODEL_SECONDARY)
        except OSError:
            nlp = spacy.blank("en")

    embedder = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
    return nlp, embedder
