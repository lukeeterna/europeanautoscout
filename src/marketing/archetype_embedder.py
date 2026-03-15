#!/usr/bin/env python3
"""
ARGOS Automotive — Archetype Embedder (TF-IDF + Semantic Retrieval)
====================================================================
Classifica l'archetipo del dealer via similarità semantica leggera.
Usa TF-IDF (sklearn) — nessuna dipendenza pesante (no torch, no chromadb).
Integra con archetype_classifier.py come fallback quando keyword conf < 0.5.

Compatibile Python 3.9+ | Dipendenze: scikit-learn, numpy (già installati)

Usage:
    # Build index (una volta, o dopo aggiornamento dataset)
    python3 src/marketing/archetype_embedder.py build

    # Test classificazione semantica
    python3 src/marketing/archetype_embedder.py "Ho già chi mi porta roba dalla Germania"

    # API
    from src.marketing.archetype_embedder import build_index, semantic_classify, hybrid_classify
    build_index()
    result = semantic_classify("Quanto guadagno io su una 530d?")
"""

import json
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ── Paths ─────────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).parent.parent.parent
_V1_FILE = _ROOT / "data" / "training" / "conversations_synthetic_v1.json"
_V2_FILE = _ROOT / "data" / "training" / "conversations_synthetic_v2.json"
_INDEX_DIR = _ROOT / "data" / "tfidf_index"
_VECTORIZER_PATH = _INDEX_DIR / "vectorizer.pkl"
_MATRIX_PATH = _INDEX_DIR / "matrix.npy"
_METADATA_PATH = _INDEX_DIR / "metadata.json"

# Cache in-memory (evita reload ad ogni chiamata)
_vectorizer: Optional[TfidfVectorizer] = None
_matrix: Optional[np.ndarray] = None
_metadata: Optional[list] = None


def _load_conversations() -> list[dict]:
    """Carica conversazioni da v1 (e v2 se disponibile)."""
    conversations = []
    for filepath in [_V1_FILE, _V2_FILE]:
        if filepath.exists():
            with open(filepath) as f:
                data = json.load(f)
            convs = data.get("conversations", [])
            conversations.extend(convs)
            print(f"[Index] Caricato {len(convs)} conv da {filepath.name}")
    return conversations


def _conv_to_text(conv: dict) -> str:
    """Trasforma una conversazione in testo per TF-IDF."""
    parts = [
        conv.get("dealer_message", ""),
        " ".join(conv.get("signals", [])),
        conv.get("context", "").replace("_", " "),
        conv.get("obj_triggered", ""),
        conv.get("primary_archetype", "").lower(),
    ]
    return " ".join(p for p in parts if p).strip()


def build_index(force_rebuild: bool = False) -> int:
    """
    Costruisce (o carica) l'index TF-IDF dalle conversazioni sintetiche.

    Returns:
        Numero di documenti indicizzati
    """
    global _vectorizer, _matrix, _metadata

    _INDEX_DIR.mkdir(parents=True, exist_ok=True)

    # Se index esiste e non forziamo rebuild → carica
    if not force_rebuild and _VECTORIZER_PATH.exists() and _MATRIX_PATH.exists():
        _vectorizer = pickle.loads(_VECTORIZER_PATH.read_bytes())
        _matrix = np.load(_MATRIX_PATH)
        with open(_METADATA_PATH) as f:
            _metadata = json.load(f)
        print(f"[Index] Caricato da disco: {len(_metadata)} documenti")
        return len(_metadata)

    conversations = _load_conversations()
    if not conversations:
        print("[Index] ERRORE: nessun dataset trovato.")
        return 0

    # Prepara corpus
    documents = []
    metadata = []
    for conv in conversations:
        text = _conv_to_text(conv)
        if not text:
            continue
        documents.append(text)
        metadata.append({
            "id": conv.get("id", ""),
            "primary_archetype": conv.get("primary_archetype", "UNKNOWN"),
            "secondary_archetype": conv.get("secondary_archetype") or "",
            "context": conv.get("context", ""),
            "obj_triggered": conv.get("obj_triggered", ""),
            "outcome_predicted": conv.get("outcome_predicted", ""),
            "dealer_message": conv.get("dealer_message", ""),
            "optimal_response": conv.get("optimal_response", ""),
        })

    # Fit TF-IDF (Italian + German terms, subword n-grams per catturare radici)
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=1,
        max_features=8000,
        sublinear_tf=True,
        analyzer="word",
        token_pattern=r"(?u)\b\w+\b"
    )
    matrix = vectorizer.fit_transform(documents)

    # Salva su disco
    _VECTORIZER_PATH.write_bytes(pickle.dumps(vectorizer))
    np.save(_MATRIX_PATH, matrix.toarray())
    with open(_METADATA_PATH, "w") as f:
        json.dump(metadata, f, ensure_ascii=False)

    # Aggiorna cache in-memory
    _vectorizer = vectorizer
    _matrix = matrix.toarray()
    _metadata = metadata

    print(f"[Index] Costruito: {len(documents)} documenti, vocab {len(vectorizer.vocabulary_)} termini")
    return len(documents)


def _ensure_index():
    """Carica l'index se non in memoria."""
    global _vectorizer, _matrix, _metadata
    if _vectorizer is None:
        build_index()


def semantic_classify(
    dealer_message: str,
    top_k: int = 5
) -> dict:
    """
    Classifica archetipo del dealer via TF-IDF cosine similarity.

    Returns:
        {
            "archetype": "RAGIONIERE",
            "confidence": 0.87,
            "context": "objection_fee",
            "archetype_vector": {...},
            "similar_cases": [...],
            "method": "tfidf"
        }
    """
    _ensure_index()

    if _vectorizer is None:
        return {"archetype": "UNKNOWN", "confidence": 0.0, "method": "tfidf", "error": "index not built"}

    # Trasforma il messaggio query
    query_vec = _vectorizer.transform([dealer_message.lower()])
    similarities = cosine_similarity(query_vec, _matrix)[0]

    # Top-k indici
    top_indices = np.argsort(similarities)[::-1][:top_k]

    # Aggrega voti per archetipo (pesati per similarity)
    archetype_votes: dict = {}
    ctx_votes: dict = {}
    similar_cases = []

    for idx in top_indices:
        sim = float(similarities[idx])
        if sim < 0.01:
            continue
        meta = _metadata[idx]
        arch = meta["primary_archetype"]
        ctx = meta.get("context", "")

        archetype_votes[arch] = archetype_votes.get(arch, 0.0) + sim
        if ctx:
            ctx_votes[ctx] = ctx_votes.get(ctx, 0.0) + sim

        similar_cases.append({
            "id": meta["id"],
            "archetype": arch,
            "context": ctx,
            "dealer_message": meta["dealer_message"],
            "optimal_response": meta["optimal_response"],
            "similarity": round(sim, 3)
        })

    if not archetype_votes:
        return {"archetype": "UNKNOWN", "confidence": 0.0, "method": "tfidf", "similar_cases": []}

    # Normalizza
    total = sum(archetype_votes.values())
    archetype_vector = {k: round(v / total, 3) for k, v in archetype_votes.items()}
    sorted_arch = sorted(archetype_vector.items(), key=lambda x: x[1], reverse=True)

    best_arch = sorted_arch[0][0]
    best_conf = sorted_arch[0][1]
    best_ctx = max(ctx_votes, key=ctx_votes.get) if ctx_votes else "day1_response"

    return {
        "archetype": best_arch,
        "confidence": round(best_conf, 3),
        "context": best_ctx,
        "archetype_vector": dict(sorted_arch),
        "similar_cases": similar_cases,
        "method": "tfidf"
    }


def hybrid_classify(
    dealer_message: str,
    keyword_result=None,
    semantic_threshold: float = 0.50,
    top_k: int = 3
) -> dict:
    """
    Classificazione ibrida: keyword first, TF-IDF fallback.

    Args:
        dealer_message: Messaggio del dealer
        keyword_result: ArchetypeResult da archetype_classifier.classify()
        semantic_threshold: Se keyword confidence < threshold → usa TF-IDF
        top_k: Casi simili da restituire

    Returns:
        dict con archetype, confidence, method, similar_cases
    """
    # Keyword con confidence alta → usalo direttamente
    if keyword_result is not None:
        conf = getattr(keyword_result, "confidence", 0.0)
        if conf >= semantic_threshold:
            return {
                "archetype": keyword_result.primary,
                "confidence": conf,
                "context": keyword_result.context,
                "method": "keyword",
                "signals": keyword_result.signals_found,
                "similar_cases": []
            }

    # Fallback TF-IDF
    semantic = semantic_classify(dealer_message, top_k=top_k)

    # Se avevamo keyword con archetipo non UNKNOWN → confronta
    if keyword_result is not None and getattr(keyword_result, "primary", "UNKNOWN") != "UNKNOWN":
        kw_arch = keyword_result.primary
        sem_arch = semantic.get("archetype", "UNKNOWN")
        kw_conf = getattr(keyword_result, "confidence", 0.0)
        sem_conf = semantic.get("confidence", 0.0)

        if kw_arch == sem_arch:
            # Concordano → boost
            semantic["confidence"] = min(1.0, round((kw_conf + sem_conf) / 2 + 0.10, 3))
            semantic["method"] = "hybrid_agree"
        elif kw_conf > sem_conf:
            semantic["archetype"] = kw_arch
            semantic["confidence"] = kw_conf
            semantic["context"] = keyword_result.context
            semantic["method"] = "hybrid_keyword_wins"
        else:
            semantic["method"] = "hybrid_semantic_wins"

    return semantic


def get_semantic_responses(
    archetype: str,
    context: str = None,
    top_k: int = 3
) -> list[dict]:
    """
    Recupera risposte ottimali per archetipo + context via similarità.
    Alternativa a archetype_classifier.get_best_response().
    """
    _ensure_index()
    if _metadata is None:
        return []

    query = f"{archetype.lower()} {(context or '').replace('_', ' ')}"
    results = semantic_classify(query, top_k=top_k * 4)

    seen = set()
    responses = []
    for case in results.get("similar_cases", []):
        if case["archetype"] != archetype:
            continue
        resp = case.get("optimal_response", "")
        if resp and resp not in seen:
            seen.add(resp)
            responses.append({
                "primary_archetype": case["archetype"],
                "context": case.get("context", ""),
                "optimal_response": resp,
                "similarity": case.get("similarity", 0.0)
            })
        if len(responses) >= top_k:
            break

    return responses


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "build":
        force = "--force" in sys.argv
        count = build_index(force_rebuild=force)
        print(f"\nIndex pronto: {count} documenti")
        sys.exit(0)

    test_msgs = [
        "Ho già chi mi porta roba dalla Germania, non ho bisogno di intermediari.",
        "Il prezzo sorgente è IVA esposta o regime margine? Cambia tutto.",
        "48 ore. Se non arriva il documento considera chiuso.",
        "Ne parlo con mio fratello, lui gestisce gli acquisti.",
        "Quanto costa? E se facciamo 3 operazioni mi fate uno sconto?",
        "Lavoro solo con persone che conosco — non ti conosco.",
        "Ho sempre fatto così, non vedo perché cambiare.",
        "Voglio essere il primo nella mia zona — esclusiva?",
    ]

    msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else test_msgs[0]
    print(f"\nInput: {msg}\n")

    # Build se necessario
    build_index()

    result = semantic_classify(msg, top_k=5)
    print(f"Archetipo:  {result['archetype']} (conf: {result['confidence']:.2f})")
    print(f"Context:    {result.get('context', '?')}")
    print(f"Metodo:     {result['method']}")
    print(f"\nVector: {result.get('archetype_vector', {})}")
    print(f"\nCasi simili:")
    for case in result.get("similar_cases", [])[:3]:
        print(f"  [{case['archetype']}] sim={case['similarity']:.3f}")
        print(f"    Dealer: {case['dealer_message'][:70]}...")
        print(f"    Risposta: {case['optimal_response'][:80]}...")
