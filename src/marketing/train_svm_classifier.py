"""
ARGOS Automotive — SVM Archetype Classifier
S55 — Training pipeline: TF-IDF + LinearSVC
Target: >97% accuracy globale, >95% per archetipo

Usage:
  python3 src/marketing/train_svm_classifier.py
  python3 src/marketing/train_svm_classifier.py --data data/training/conversations_synthetic_v2.json
  python3 src/marketing/train_svm_classifier.py --evaluate-only --model data/models/argos_svm_classifier.pkl
"""

import json
import os
import sys
import pickle
import argparse
from pathlib import Path

import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import (
    classification_report, confusion_matrix,
    accuracy_score, f1_score
)
from sklearn.preprocessing import LabelEncoder

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "training"
MODEL_DIR = BASE_DIR / "data" / "models"
MODEL_PATH = MODEL_DIR / "argos_svm_classifier.pkl"

DATASET_V1 = DATA_DIR / "conversations_synthetic_v1.json"
DATASET_V2 = DATA_DIR / "conversations_synthetic_v2.json"

ARCHETYPES = [
    "RAGIONIERE", "BARONE", "PERFORMANTE", "NARCISO", "TECNICO",
    "RELAZIONALE", "CONSERVATORE", "DELEGATORE", "OPPORTUNISTA", "VISIONARIO"
]

# ── Data loading ───────────────────────────────────────────────────────────────

def load_dataset(path: Path) -> list[dict]:
    """Load conversations from a JSON dataset file."""
    if not path.exists():
        print(f"  [SKIP] {path.name} not found")
        return []
    with open(path) as f:
        data = json.load(f)
    convs = data.get("conversations", data) if isinstance(data, dict) else data
    print(f"  [LOAD] {path.name}: {len(convs)} conversations")
    return convs


def build_corpus(conversations: list[dict]) -> tuple[list[str], list[str]]:
    """
    Extract (text, label) pairs from conversations.
    Text = dealer_message + signals joined.
    Label = primary_archetype.
    """
    texts, labels = [], []
    for conv in conversations:
        archetype = conv.get("primary_archetype", "").strip().upper()
        if archetype not in ARCHETYPES:
            continue
        msg = conv.get("dealer_message", "").strip()
        signals = " ".join(conv.get("signals", []))
        # Concatenate dealer message + signals for richer features
        text = f"{msg} {signals}".strip()
        if text:
            texts.append(text)
            labels.append(archetype)
    return texts, labels


def load_all_data(extra_paths: list[Path] | None = None) -> tuple[list[str], list[str]]:
    """Load v1 + v2 + any extra datasets."""
    all_convs = []
    for path in [DATASET_V1, DATASET_V2]:
        all_convs.extend(load_dataset(path))
    if extra_paths:
        for path in extra_paths:
            all_convs.extend(load_dataset(path))
    print(f"  [TOTAL] {len(all_convs)} conversations loaded")
    return build_corpus(all_convs)


# ── Pipeline ───────────────────────────────────────────────────────────────────

def build_pipeline() -> Pipeline:
    """TF-IDF + CalibratedLinearSVC pipeline."""
    return Pipeline([
        ('tfidf', TfidfVectorizer(
            ngram_range=(1, 3),
            sublinear_tf=True,
            max_features=15000,
            min_df=1,
            analyzer='word',
            token_pattern=r'(?u)\b\w+\b',
            strip_accents=None,
        )),
        ('svm', CalibratedClassifierCV(
            LinearSVC(
                C=1.0,
                class_weight='balanced',
                max_iter=2000,
                random_state=42,
            ),
            cv=3,
            method='isotonic',
        )),
    ])


# ── Training ───────────────────────────────────────────────────────────────────

def train(texts: list[str], labels: list[str]) -> Pipeline:
    """Train on full dataset and return fitted pipeline."""
    print(f"\n[TRAIN] Fitting on {len(texts)} samples...")
    pipeline = build_pipeline()
    pipeline.fit(texts, labels)
    print("  [DONE] Pipeline fitted.")
    return pipeline


def cross_val_report(texts: list[str], labels: list[str]) -> dict:
    """StratifiedKFold(5) cross-validation with per-class report."""
    print(f"\n[CV] StratifiedKFold(5) cross-validation on {len(texts)} samples...")
    pipeline = build_pipeline()
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    results = cross_validate(
        pipeline, texts, labels,
        cv=skf,
        scoring=['accuracy', 'f1_macro', 'f1_weighted'],
        return_train_score=True,
        n_jobs=-1,
    )

    print(f"\n{'─'*60}")
    print("CROSS-VALIDATION RESULTS (5-fold)")
    print(f"{'─'*60}")
    print(f"  Train accuracy:    {results['train_accuracy'].mean():.4f} ± {results['train_accuracy'].std():.4f}")
    print(f"  Test  accuracy:    {results['test_accuracy'].mean():.4f} ± {results['test_accuracy'].std():.4f}")
    print(f"  Test  F1 macro:    {results['test_f1_macro'].mean():.4f} ± {results['test_f1_macro'].std():.4f}")
    print(f"  Test  F1 weighted: {results['test_f1_weighted'].mean():.4f} ± {results['test_f1_weighted'].std():.4f}")

    # Per-archetype breakdown using last fold
    skf2 = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    last_train, last_test = list(skf2.split(texts, labels))[-1]
    X_tr = [texts[i] for i in last_train]
    y_tr = [labels[i] for i in last_train]
    X_te = [texts[i] for i in last_test]
    y_te = [labels[i] for i in last_test]

    pipeline.fit(X_tr, y_tr)
    y_pred = pipeline.predict(X_te)

    print(f"\n{'─'*60}")
    print("PER-ARCHETYPE REPORT (last fold)")
    print(f"{'─'*60}")
    report = classification_report(y_te, y_pred, target_names=sorted(set(labels)), zero_division=0)
    print(report)

    # Check target
    acc = accuracy_score(y_te, y_pred)
    target_met = acc >= 0.97
    print(f"  Global accuracy: {acc:.4f} {'✅ TARGET MET (≥97%)' if target_met else '⚠️  BELOW TARGET'}")

    # Per-class check
    from sklearn.metrics import classification_report as cr
    cr_dict = classification_report(y_te, y_pred, target_names=sorted(set(labels)),
                                    zero_division=0, output_dict=True)
    print(f"\n  Per-archetype accuracy (recall):")
    all_ok = True
    for arch in sorted(set(labels)):
        r = cr_dict.get(arch, {}).get('recall', 0)
        ok = r >= 0.95
        if not ok:
            all_ok = False
        print(f"    {arch:<15} {r:.4f} {'✅' if ok else '⚠️  <95%'}")

    print(f"\n  All archetypes ≥95%: {'✅ YES' if all_ok else '❌ NO — need more data or tuning'}")

    return {
        'cv_accuracy_mean': results['test_accuracy'].mean(),
        'cv_accuracy_std': results['test_accuracy'].std(),
        'target_met': target_met,
        'all_archetypes_ok': all_ok,
    }


# ── Persistence ────────────────────────────────────────────────────────────────

def save_model(pipeline: Pipeline, path: Path, metadata: dict | None = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'pipeline': pipeline,
        'archetypes': ARCHETYPES,
        'metadata': metadata or {},
    }
    with open(path, 'wb') as f:
        pickle.dump(payload, f)
    size_kb = path.stat().st_size / 1024
    print(f"\n[SAVE] Model saved → {path} ({size_kb:.1f} KB)")


def load_model(path: Path) -> tuple[Pipeline, list[str]]:
    with open(path, 'rb') as f:
        payload = pickle.load(f)
    return payload['pipeline'], payload['archetypes']


# ── Inference ──────────────────────────────────────────────────────────────────

def predict(pipeline: Pipeline, text: str) -> dict:
    """Predict archetype with confidence probabilities."""
    probs = pipeline.predict_proba([text])[0]
    classes = pipeline.classes_
    top_idx = np.argsort(probs)[::-1]
    return {
        'archetype': classes[top_idx[0]],
        'confidence': float(probs[top_idx[0]]),
        'top3': [
            {'archetype': classes[i], 'prob': float(probs[i])}
            for i in top_idx[:3]
        ]
    }


# ── Evaluation on real dealer messages ────────────────────────────────────────

REAL_DEALER_TEST = [
    # Mazzilli Auto — PERFORMANTE expected
    ("Guarda ho bisogno di 2 BMW 520d entro fine mese o considera chiuso. Quante ne hai adesso?", "PERFORMANTE"),
    # Prime Cars Italy — TECNICO expected
    ("Mi specifichi quali enti certificatori usate. Il Gutachten lo emette DEKRA o TÜV? E chi firma il contratto?", "TECNICO"),
    # Campania Sport Car — RAGIONIERE expected
    ("Come funziona l'IVA su questa operazione? Mi serve un prospetto con il margine netto reale.", "RAGIONIERE"),
    # BARONE test
    ("Ho già i miei fornitori da anni. Non vedo cosa cambia.", "BARONE"),
    # NARCISO test
    ("La mia clientela è esigente. Come appare il veicolo? Il cliente finale non deve sapere che viene dall'estero.", "NARCISO"),
    # RELAZIONALE test
    ("Non la conosco. Ha referenze di dealer con cui ha già lavorato qui al Sud?", "RELAZIONALE"),
    # CONSERVATORE test
    ("Ho sempre fatto così e non ho problemi. Perché dovrei cambiare?", "CONSERVATORE"),
    # DELEGATORE test
    ("Mi mandi qualcosa che posso girare al mio socio. Non decido da solo queste cose.", "DELEGATORE"),
    # OPPORTUNISTA test
    ("Quanto costa esattamente? Se faccio 3 operazioni mi fa uno sconto?", "OPPORTUNISTA"),
    # VISIONARIO test
    ("Voglio essere il primo nella mia zona a fare questa cosa. Posso avere l'esclusiva?", "VISIONARIO"),
]


def evaluate_real_messages(pipeline: Pipeline):
    print(f"\n{'─'*60}")
    print("REAL DEALER MESSAGE TEST")
    print(f"{'─'*60}")
    correct = 0
    for text, expected in REAL_DEALER_TEST:
        result = predict(pipeline, text)
        got = result['archetype']
        ok = got == expected
        correct += ok
        status = "✅" if ok else f"❌ got {got}"
        print(f"  [{status}] {expected:<15} conf={result['confidence']:.3f} | {text[:60]}...")
    print(f"\n  Score: {correct}/{len(REAL_DEALER_TEST)} ({correct/len(REAL_DEALER_TEST)*100:.0f}%)")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='ARGOS SVM Classifier Trainer')
    parser.add_argument('--data', type=str, help='Extra dataset path')
    parser.add_argument('--evaluate-only', action='store_true', help='Skip training, evaluate existing model')
    parser.add_argument('--model', type=str, default=str(MODEL_PATH), help='Model path')
    parser.add_argument('--no-cv', action='store_true', help='Skip cross-validation (faster)')
    args = parser.parse_args()

    model_path = Path(args.model)

    print("=" * 60)
    print("ARGOS SVM Archetype Classifier — S55")
    print("=" * 60)

    if args.evaluate_only:
        if not model_path.exists():
            print(f"[ERROR] Model not found: {model_path}")
            sys.exit(1)
        print(f"[LOAD] Loading model from {model_path}")
        pipeline, _ = load_model(model_path)
        evaluate_real_messages(pipeline)
        return

    # Load data
    print("\n[DATA] Loading datasets...")
    extra = [Path(args.data)] if args.data else None
    texts, labels = load_all_data(extra)

    if len(texts) < 10:
        print("[ERROR] Not enough training data. Need at least 10 samples.")
        sys.exit(1)

    # Label distribution
    from collections import Counter
    dist = Counter(labels)
    print(f"\n[DATA] Label distribution:")
    for arch in ARCHETYPES:
        n = dist.get(arch, 0)
        bar = "█" * (n // 5)
        print(f"  {arch:<15} {n:>4} {bar}")

    # Cross-validation
    cv_results = {}
    if not args.no_cv:
        cv_results = cross_val_report(texts, labels)

    # Train on full data
    pipeline = train(texts, labels)

    # Save
    metadata = {
        'n_samples': len(texts),
        'archetypes': ARCHETYPES,
        'cv_results': cv_results,
        'generated_at': '2026-03-15',
    }
    save_model(pipeline, model_path, metadata)

    # Evaluate on real messages
    evaluate_real_messages(pipeline)

    print(f"\n{'='*60}")
    if cv_results.get('target_met'):
        print("✅ TARGET REACHED: accuracy ≥97% — ready for production")
    else:
        acc = cv_results.get('cv_accuracy_mean', 0)
        needed = max(0, 0.97 - acc)
        print(f"⚠️  accuracy={acc:.4f} — need +{needed:.4f} → add more data or tune C param")
    print("=" * 60)


if __name__ == '__main__':
    main()
