#!/bin/bash
# PostToolUse hook — COMBARETROVAMIAUTO
# Eseguito automaticamente dopo ogni Write su file .py
# Posizione: .claude/hooks/post-write-python.sh

FILE="$1"

# Esegui solo su file Python
if [[ "$FILE" != *.py ]]; then
  exit 0
fi

# Syntax check immediato
python3 -m py_compile "$FILE"
if [ $? -ne 0 ]; then
  echo "❌ SYNTAX ERROR in $FILE — fix before proceeding"
  exit 1
fi

# Controlla anti-pattern CoVe
if grep -q "verdict" "$FILE" 2>/dev/null && ! grep -q "# noqa-cove" "$FILE"; then
  echo "⚠️  WARNING: 'verdict' trovato in $FILE — usa 'recommendation' (schema CoVe v4)"
fi

if grep -q "created_at" "$FILE" 2>/dev/null && grep -q "cove_results" "$FILE" 2>/dev/null; then
  echo "⚠️  WARNING: 'created_at' su cove_results in $FILE — usa 'analyzed_at'"
fi

echo "✅ $FILE — syntax OK"
