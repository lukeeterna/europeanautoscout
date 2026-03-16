"""
ARGOS Automotive — SVM Archetype Classifier v2
S58 — Sentence-Transformers + LinearSVC
Model: paraphrase-multilingual-MiniLM-L12-v2 (420MB, offline, IT nativo)

Architettura:
  sentence-transformers → embeddings 384d → LinearSVC
  vs TF-IDF (v1) → ngram bag-of-words → LinearSVC

Target: >85% CV accuracy (vs 79.6% TF-IDF ceiling)

NOTA: Richiede Python 3.11 (torch non disponibile su Python 3.13 + macOS Big Sur x86_64)

Usage:
  python3.11 src/marketing/train_svm_v2_sentence.py
  python3.11 src/marketing/train_svm_v2_sentence.py --compare  (confronto TF-IDF vs sentence-transformers)
  python3.11 src/marketing/train_svm_v2_sentence.py --evaluate-only --model data/models/argos_svm_v2_sentence.pkl
"""

import json
import os
import sys
import pickle
import argparse
import time
from pathlib import Path

import numpy as np
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
from collections import Counter

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "training"
MODEL_DIR = BASE_DIR / "data" / "models"
MODEL_PATH_V2 = MODEL_DIR / "argos_svm_v2_sentence.pkl"
MODEL_PATH_V1 = MODEL_DIR / "argos_svm_classifier.pkl"

DATASET_V1 = DATA_DIR / "conversations_synthetic_v1.json"
DATASET_V2 = DATA_DIR / "conversations_synthetic_v2.json"

ARCHETYPES = [
    "RAGIONIERE", "BARONE", "PERFORMANTE", "NARCISO", "TECNICO",
    "RELAZIONALE", "CONSERVATORE", "DELEGATORE", "OPPORTUNISTA", "VISIONARIO"
]

# Sentence-transformers model — multilingual, IT nativo, 420MB, offline
SENTENCE_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


# ── Data loading ───────────────────────────────────────────────────────────────

def load_dataset(path: Path) -> list:
    if not path.exists():
        print(f"  [SKIP] {path.name} not found")
        return []
    with open(path) as f:
        data = json.load(f)
    convs = data.get("conversations", data) if isinstance(data, dict) else data
    print(f"  [LOAD] {path.name}: {len(convs)} conversations")
    return convs


def build_corpus(conversations: list) -> tuple:
    texts, labels = [], []
    for conv in conversations:
        archetype = conv.get("primary_archetype", "").strip().upper()
        if archetype not in ARCHETYPES:
            continue
        msg = conv.get("dealer_message", "").strip()
        signals = " ".join(conv.get("signals", []))
        text = f"{msg} {signals}".strip()
        if text:
            texts.append(text)
            labels.append(archetype)
    return texts, labels


def load_all_data(extra_paths=None):
    all_convs = []
    for path in [DATASET_V1, DATASET_V2]:
        all_convs.extend(load_dataset(path))
    if extra_paths:
        for path in extra_paths:
            all_convs.extend(load_dataset(path))
    print(f"  [TOTAL] {len(all_convs)} conversations loaded")
    return build_corpus(all_convs)


# ── Sentence-Transformers Embedding ───────────────────────────────────────────

def get_embeddings(texts: list, model_name: str = SENTENCE_MODEL, batch_size: int = 64):
    """Compute sentence embeddings. Downloads model on first use (~420MB)."""
    from sentence_transformers import SentenceTransformer

    print(f"\n[EMBED] Loading model: {model_name}")
    t0 = time.time()
    model = SentenceTransformer(model_name)
    print(f"  Model loaded in {time.time() - t0:.1f}s")

    print(f"[EMBED] Encoding {len(texts)} texts (batch_size={batch_size})...")
    t0 = time.time()
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=True)
    elapsed = time.time() - t0
    print(f"  Encoded in {elapsed:.1f}s ({len(texts)/elapsed:.0f} texts/sec)")
    print(f"  Embedding shape: {embeddings.shape}")

    return embeddings, model


# ── Pipeline ──────────────────────────────────────────────────────────────────

def build_svm():
    """CalibratedLinearSVC for archetype classification."""
    return CalibratedClassifierCV(
        LinearSVC(
            C=1.0,
            class_weight='balanced',
            max_iter=2000,
            random_state=42,
        ),
        cv=3,
        method='isotonic',
    )


# ── Cross-validation ─────────────────────────────────────────────────────────

def cross_val_report(X, labels):
    """StratifiedKFold(5) cross-validation on embeddings."""
    print(f"\n[CV] StratifiedKFold(5) on {len(labels)} samples, {X.shape[1]}d embeddings...")
    svm = build_svm()
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    results = cross_validate(
        svm, X, labels,
        cv=skf,
        scoring=['accuracy', 'f1_macro', 'f1_weighted'],
        return_train_score=True,
        n_jobs=-1,
    )

    print(f"\n{'─'*60}")
    print("CROSS-VALIDATION RESULTS — SENTENCE-TRANSFORMERS + SVM")
    print(f"{'─'*60}")
    print(f"  Train accuracy:    {results['train_accuracy'].mean():.4f} ± {results['train_accuracy'].std():.4f}")
    print(f"  Test  accuracy:    {results['test_accuracy'].mean():.4f} ± {results['test_accuracy'].std():.4f}")
    print(f"  Test  F1 macro:    {results['test_f1_macro'].mean():.4f} ± {results['test_f1_macro'].std():.4f}")
    print(f"  Test  F1 weighted: {results['test_f1_weighted'].mean():.4f} ± {results['test_f1_weighted'].std():.4f}")

    # Per-archetype breakdown using last fold
    skf2 = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    last_train, last_test = list(skf2.split(X, labels))[-1]
    X_tr, y_tr = X[last_train], [labels[i] for i in last_train]
    X_te, y_te = X[last_test], [labels[i] for i in last_test]

    svm_eval = build_svm()
    svm_eval.fit(X_tr, y_tr)
    y_pred = svm_eval.predict(X_te)

    print(f"\n{'─'*60}")
    print("PER-ARCHETYPE REPORT (last fold)")
    print(f"{'─'*60}")
    print(classification_report(y_te, y_pred, zero_division=0))

    return {
        'cv_accuracy_mean': results['test_accuracy'].mean(),
        'cv_accuracy_std': results['test_accuracy'].std(),
        'cv_f1_macro': results['test_f1_macro'].mean(),
    }


# ── Compare TF-IDF vs Sentence-Transformers ──────────────────────────────────

def compare_with_tfidf(texts, labels, embeddings):
    """Side-by-side comparison TF-IDF vs sentence-transformers."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.pipeline import Pipeline

    print(f"\n{'='*60}")
    print("CONFRONTO DIRETTO: TF-IDF vs SENTENCE-TRANSFORMERS")
    print(f"{'='*60}")

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # TF-IDF
    print("\n[1/2] TF-IDF + LinearSVC...")
    tfidf_pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            ngram_range=(1, 3), sublinear_tf=True,
            max_features=15000, min_df=1,
        )),
        ('svm', CalibratedClassifierCV(
            LinearSVC(C=1.0, class_weight='balanced', max_iter=2000, random_state=42),
            cv=3, method='isotonic',
        )),
    ])
    tfidf_results = cross_validate(
        tfidf_pipeline, texts, labels, cv=skf,
        scoring=['accuracy', 'f1_macro'], n_jobs=-1,
    )
    tfidf_acc = tfidf_results['test_accuracy'].mean()
    tfidf_f1 = tfidf_results['test_f1_macro'].mean()

    # Sentence-transformers
    print("[2/2] Sentence-Transformers + LinearSVC...")
    sent_svm = build_svm()
    sent_results = cross_validate(
        sent_svm, embeddings, labels, cv=skf,
        scoring=['accuracy', 'f1_macro'], n_jobs=-1,
    )
    sent_acc = sent_results['test_accuracy'].mean()
    sent_f1 = sent_results['test_f1_macro'].mean()

    # Results
    delta_acc = sent_acc - tfidf_acc
    delta_f1 = sent_f1 - tfidf_f1

    print(f"\n{'─'*60}")
    print(f"{'Metric':<25} {'TF-IDF':>10} {'SentTransf':>12} {'Delta':>10}")
    print(f"{'─'*60}")
    print(f"{'CV Accuracy':<25} {tfidf_acc:>10.4f} {sent_acc:>12.4f} {delta_acc:>+10.4f}")
    print(f"{'CV F1 Macro':<25} {tfidf_f1:>10.4f} {sent_f1:>12.4f} {delta_f1:>+10.4f}")
    print(f"{'─'*60}")

    if delta_acc > 0.02:
        print(f"\n✅ SENTENCE-TRANSFORMERS VINCE con +{delta_acc:.1%} accuracy")
        print("   → Raccomandazione: SOSTITUIRE TF-IDF in produzione")
    elif delta_acc > 0:
        print(f"\n⚠️  Sentence-transformers leggermente meglio (+{delta_acc:.1%})")
        print("   → Valutare se il costo computazionale giustifica il miglioramento")
    else:
        print(f"\n❌ TF-IDF è uguale o migliore — non sostituire")

    return {
        'tfidf_accuracy': tfidf_acc, 'tfidf_f1': tfidf_f1,
        'sent_accuracy': sent_acc, 'sent_f1': sent_f1,
        'delta_accuracy': delta_acc, 'delta_f1': delta_f1,
    }


# ── Real dealer test ─────────────────────────────────────────────────────────

REAL_DEALER_TEST = [
    ("Guarda ho bisogno di 2 BMW 520d entro fine mese o considera chiuso. Quante ne hai adesso?", "PERFORMANTE"),
    ("Mi specifichi quali enti certificatori usate. Il Gutachten lo emette DEKRA o TÜV? E chi firma il contratto?", "TECNICO"),
    ("Come funziona l'IVA su questa operazione? Mi serve un prospetto con il margine netto reale.", "RAGIONIERE"),
    ("Ho già i miei fornitori da anni. Non vedo cosa cambia.", "BARONE"),
    ("La mia clientela è esigente. Come appare il veicolo? Il cliente finale non deve sapere che viene dall'estero.", "NARCISO"),
    ("Non la conosco. Ha referenze di dealer con cui ha già lavorato qui al Sud?", "RELAZIONALE"),
    ("Ho sempre fatto così e non ho problemi. Perché dovrei cambiare?", "CONSERVATORE"),
    ("Mi mandi qualcosa che posso girare al mio socio. Non decido da solo queste cose.", "DELEGATORE"),
    ("Quanto costa esattamente? Se faccio 3 operazioni mi fa uno sconto?", "OPPORTUNISTA"),
    ("Voglio essere il primo nella mia zona a fare questa cosa. Posso avere l'esclusiva?", "VISIONARIO"),
]


def evaluate_real(svm, sentence_model):
    """Test su messaggi dealer realistici."""
    from sentence_transformers import SentenceTransformer

    print(f"\n{'─'*60}")
    print("REAL DEALER MESSAGE TEST — SENTENCE-TRANSFORMERS")
    print(f"{'─'*60}")

    texts = [t for t, _ in REAL_DEALER_TEST]
    expected = [e for _, e in REAL_DEALER_TEST]

    embeddings = sentence_model.encode(texts, show_progress_bar=False)
    predictions = svm.predict(embeddings)

    if hasattr(svm, 'predict_proba'):
        probas = svm.predict_proba(embeddings)
        classes = svm.classes_
    else:
        probas = None
        classes = None

    correct = 0
    for i, (text, exp) in enumerate(REAL_DEALER_TEST):
        pred = predictions[i]
        ok = pred == exp
        correct += ok

        conf = ""
        if probas is not None:
            idx = list(classes).index(pred)
            conf = f" conf={probas[i][idx]:.3f}"

        status = "✅" if ok else f"❌ got {pred}"
        print(f"  [{status}] {exp:<15}{conf} | {text[:55]}...")

    print(f"\n  Score: {correct}/{len(REAL_DEALER_TEST)} ({correct/len(REAL_DEALER_TEST)*100:.0f}%)")


# ── Persistence ──────────────────────────────────────────────────────────────

def save_model(svm, sentence_model_name, path, metadata=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'svm': svm,
        'sentence_model_name': sentence_model_name,
        'archetypes': ARCHETYPES,
        'metadata': metadata or {},
        'version': 'v2_sentence_transformers',
    }
    with open(path, 'wb') as f:
        pickle.dump(payload, f)
    size_kb = path.stat().st_size / 1024
    print(f"\n[SAVE] Model saved → {path} ({size_kb:.1f} KB)")
    print(f"  Note: sentence-transformers model '{sentence_model_name}' must be available at inference time")


def load_model(path):
    with open(path, 'rb') as f:
        payload = pickle.load(f)
    return payload['svm'], payload['sentence_model_name'], payload['archetypes']


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='ARGOS SVM v2 — Sentence-Transformers')
    parser.add_argument('--data', type=str, help='Extra dataset path')
    parser.add_argument('--compare', action='store_true', help='Compare TF-IDF vs sentence-transformers')
    parser.add_argument('--evaluate-only', action='store_true')
    parser.add_argument('--model', type=str, default=str(MODEL_PATH_V2))
    parser.add_argument('--no-cv', action='store_true')
    args = parser.parse_args()

    print("=" * 60)
    print("ARGOS SVM v2 — Sentence-Transformers Classifier")
    print(f"Model: {SENTENCE_MODEL}")
    print("=" * 60)

    if args.evaluate_only:
        model_path = Path(args.model)
        if not model_path.exists():
            print(f"[ERROR] Model not found: {model_path}")
            sys.exit(1)
        svm, model_name, _ = load_model(model_path)
        from sentence_transformers import SentenceTransformer
        sent_model = SentenceTransformer(model_name)
        evaluate_real(svm, sent_model)
        return

    # Load data
    print("\n[DATA] Loading datasets...")
    extra = [Path(args.data)] if args.data else None
    texts, labels = load_all_data(extra)

    if len(texts) < 10:
        print("[ERROR] Not enough data.")
        sys.exit(1)

    # Distribution
    dist = Counter(labels)
    print(f"\n[DATA] Label distribution:")
    for arch in ARCHETYPES:
        n = dist.get(arch, 0)
        bar = "█" * (n // 5)
        print(f"  {arch:<15} {n:>4} {bar}")

    # Compute embeddings
    embeddings, sentence_model = get_embeddings(texts)

    # Compare mode
    if args.compare:
        compare_with_tfidf(texts, labels, embeddings)

    # Cross-validation
    cv_results = {}
    if not args.no_cv:
        cv_results = cross_val_report(embeddings, labels)

    # Train on full data
    print(f"\n[TRAIN] Fitting SVM on {len(texts)} samples ({embeddings.shape[1]}d)...")
    svm = build_svm()
    svm.fit(embeddings, labels)
    print("  [DONE] SVM fitted.")

    # Save
    metadata = {
        'n_samples': len(texts),
        'embedding_dim': embeddings.shape[1],
        'sentence_model': SENTENCE_MODEL,
        'cv_results': cv_results,
    }
    save_model(svm, SENTENCE_MODEL, Path(args.model), metadata)

    # Real dealer test
    evaluate_real(svm, sentence_model)

    print(f"\n{'='*60}")
    acc = cv_results.get('cv_accuracy_mean', 0)
    if acc >= 0.85:
        print(f"✅ TARGET RAGGIUNTO: {acc:.1%} — sentence-transformers GO per produzione")
    elif acc >= 0.80:
        print(f"⚠️  {acc:.1%} — miglioramento rispetto a TF-IDF ma sotto target 85%")
    else:
        print(f"❌ {acc:.1%} — serve più data o tuning")
    print("=" * 60)


if __name__ == '__main__':
    main()
