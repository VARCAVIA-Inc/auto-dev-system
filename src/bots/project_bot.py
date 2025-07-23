import os
import yaml
import logging
import subprocess
import re
from src.utils.git_utils import commit_and_push_changes
from src.utils.ai_utils import get_gemini_model, generate_response, PLANNING_MODEL

def is_plan_valid(plan_text: str) -> bool:
    # (Funzione invariata, la ometto per brevità ma va inclusa nel file)
    logging.info("Validazione del piano di sviluppo generato...")
    has_tasks = False
    for line in plan_text.splitlines():
        line = line.strip()
        if not line: continue
        if line.startswith("- [ ]"):
            has_tasks = True
            if not re.match(r'^\s*-\s*\[\s*\]\s*\[(.+?)\]', line):
                logging.error(f"Riga di task non valida trovata: '{line}'. Formato non corretto.")
                return False
    if not has_tasks:
        logging.error("Validazione fallita: il piano non contiene task azionabili ('- [ ]').")
    return has_tasks

def update_business_plan_status(task_index, phase_index, new_status):
    # (Funzione invariata, la ometto per brevità ma va inclusa nel file)
    pass # Placeholder

def run_project_bot(task_details, task_index, phase_index):
    task_description = task_details.get('description', 'N/A')
    logging.info(f"--- ProjectBot: Inizio Pianificazione per '{task_description}' ---")

    try:
        gemini_model = get_gemini_model(PLANNING_MODEL)
        repo_root = os.getenv('GITHUB_WORKSPACE', os.getcwd())
        result = subprocess.run(['ls', '-laR'], cwd=repo_root, capture_output=True, text=True, check=True)
        file_structure = result.stdout
    except Exception as e:
        logging.error(f"Errore nella preparazione della pianificazione: {e}")
        update_business_plan_status(task_index, phase_index, "planning_failed")
        return

    # --- PROMPT POTENZIATO CON LA REGOLA '.gitkeep' ---
    prompt = (
        f"Sei il ProjectBot (CTO). Traduci un obiettivo di business in un piano tecnico in Markdown per gli OperatorBot.\n"
        f"Struttura del progetto attuale:\n```\n{file_structure}\n```\n\n"
        f"Obiettivo di Business: '{task_description}'.\n\n"
        f"**REGOLE CRITICHE E OBBLIGATORIE PER IL PIANO:**\n"
        f"1. Il piano DEVE contenere una lista di sotto-task azionabili.\n"
        f"2. OGNI SINGOLO SOTTO-TASK DEVE iniziare con '- [ ]' seguito IMMEDIATAMENTE da un marcatore tra parentesi quadre, come '[percorso/del/file.py]' o '[shell-command]'.\n"
        f"3. Per ogni file di codice sorgente, DEVI includere un task successivo per un file di test corrispondente (es. `[tests/bots/test_mio_file.py]`).\n"
        f"4. **NUOVA REGOLA GIT:** Se crei una nuova cartella con `mkdir`, DEVI aggiungere un task immediatamente successivo per creare un file vuoto '.gitkeep' al suo interno. Esempio: '- [ ] [shell-command] touch path/to/new_dir/.gitkeep'.\n"
        f"5. Il comando in un task '[shell-command]' DEVE essere puro, senza virgolette inverse (backticks)."
    )

    piano_generato = generate_response(gemini_model, prompt)
    
    if not piano_generato or not is_plan_valid(piano_generato):
        logging.error("Fallimento nella generazione del piano: l'output dell'IA è vuoto o non valido.")
        update_business_plan_status(task_index, phase_index, "planning_failed")
        return

    plan_path = os.path.join(repo_root, 'development_plan.md')
    with open(plan_path, 'w') as f:
        f.write(piano_generato)
    logging.info(f"Piano di sviluppo TDD valido salvato in '{plan_path}'")

    update_business_plan_status(task_index, phase_index, "planned")
    commit_message = f"feat(project): Generato piano TDD valido per '{task_description[:45]}...'"
    commit_and_push_changes(repo_root, commit_message, "main")
    
    logging.info(f"--- ProjectBot: Pianificazione TDD completata. ---")