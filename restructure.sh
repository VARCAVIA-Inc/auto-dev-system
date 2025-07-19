#!/bin/bash

echo "🚀 Inizio ristrutturazione del progetto VARCAVIA Office..."
echo ""

# --- 1. Creazione delle nuove cartelle e dei file __init__.py ---
echo "-> Creazione di 'src/bots', 'src/utils' e dei file __init__.py..."
mkdir -p src/bots
mkdir -p src/utils
touch src/bots/__init__.py
touch src/utils/__init__.py
echo ""

# --- 2. Spostamento dei file dei bot ---
echo "-> Spostamento degli script dei bot in 'src/bots/'..."
# Sposta i file solo se esistono nella vecchia posizione
[ -f src/manager_bot.py ] && mv src/manager_bot.py src/bots/
[ -f src/project_bot.py ] && mv src/project_bot.py src/bots/
[ -f src/operator_bot.py ] && mv src/operator_bot.py src/bots/
[ -f src/audit_bot.py ] && mv src/audit_bot.py src/bots/
echo ""

# --- 3. Spostamento dei file di utility ---
echo "-> Spostamento degli script di utility in 'src/utils/'..."
[ -f src/ai_utils.py ] && mv src/ai_utils.py src/utils/
[ -f src/git_utils.py ] && mv src/git_utils.py src/utils/
[ -f src/logging_utils.py ] && mv src/logging_utils.py src/utils/
echo ""

# --- 4. Aggiornamento dei percorsi nei workflow di GitHub Actions ---
echo "-> Aggiornamento dei percorsi degli script nei file di workflow..."
# Applica la sostituzione a tutti i file .yml nella cartella workflows
for workflow_file in .github/workflows/*.yml; do
  if [ -f "$workflow_file" ]; then
    echo "   - Analizzo $workflow_file"
    sed -i 's|src/manager_bot.py|src/bots/manager_bot.py|g' "$workflow_file"
    sed -i 's|src/project_bot.py|src/bots/project_bot.py|g' "$workflow_file"
    sed -i 's|src/operator_bot.py|src/bots/operator_bot.py|g' "$workflow_file"
    sed -i 's|src/audit_bot.py|src/bots/audit_bot.py|g' "$workflow_file"
  fi
done
echo ""

# --- 5. Verifica finale ---
echo "✅ Ristrutturazione completata."
echo "Ecco la nuova struttura della cartella 'src/':"
ls -R src/
echo ""
echo "Ora puoi procedere a incollare il contenuto aggiornato dei file che ti ho fornito in precedenza."