import os
import yaml
import logging
import subprocess
from src.utils.git_utils import commit_and_push_changes
from src.utils.ai_utils import get_gemini_model, generate_response, PLANNING_MODEL

def update_business_plan_status(task_index, phase_index, new_status="planned"):
    # (Codice invariato)
    repo_root = os.getenv('GITHUB_WORKSPACE', os.getcwd())
    business_plan_path = os.path.join(repo_root, 'src', 'business_plan.yaml')
    try:
        with open(business_plan_path, 'r') as file:
            plan = yaml.safe_load(file)
        plan['phases'][phase_index]['tasks'][task_index]['status'] = new_status
        with open(business_plan_path, 'w') as file:
            yaml.dump(plan, file, default_flow_style=False, sort_keys=False)
        logging.info(f"Stato del task aggiornato a '{new_status}'.")
        return True
    except Exception as e:
        logging.error(f"Errore durante l'aggiornamento del Business Plan: {e}", exc_info=True)
        return False

def run_project_bot(task_details, task_index, phase_index):
    task_description = task_details.get('description', 'N/A')
    logging.info(f"--- ProjectBot: Inizio Pianificazione per '{task_description}' ---")

    try:
        gemini_model = get_gemini_model(PLANNING_MODEL)
    except Exception:
        update_business_plan_status(task_index, phase_index, "planning_failed")
        return

    repo_root = os.getenv('GITHUB_WORKSPACE', os.getcwd())
    try:
        result = subprocess.run(['ls', '-R'], cwd=repo_root, capture_output=True, text=True, check=True)
        file_structure = result.stdout
    except Exception as e:
        file_structure = f"Impossibile leggere la struttura dei file: {e}"

    prompt = (
        f"Sei il ProjectBot (CTO). Traduci un obiettivo di business in un piano tecnico in Markdown per i tuoi OperatorBot. "
        f"L'obiettivo è implementare uno sviluppo guidato dai test (TDD).\n"
        f"Struttura del progetto attuale:\n```\n{file_structure}\n```\n\n"
        f"Obiettivo di Business: '{task_description}'.\n\n"
        f"**REGOLE CRITICHE PER IL PIANO:**\n"
        f"1. Il piano DEVE contenere una lista di sotto-task azionabili.\n"
        f"2. Ogni sotto-task DEVE iniziare con '- [ ]'.\n"
        f"3. Per ogni file di codice sorgente (es. `[src/bots/mio_file.py]`), DEVI includere un task successivo per un file di test corrispondente (es. `[src/bots/test_mio_file.py]`).\n"
        f"4. I file di test devono usare la libreria `pytest`.\n"
        f"5. Per comandi di sistema, usa '[shell-command]'. Il comando deve essere puro, senza virgolette inverse (backticks)."
    )

    piano_generato = generate_response(gemini_model, prompt)
    
    # --- NUOVO CONTROLLO DI VALIDITÀ ---
    if not piano_generato or "- [ ]" not in piano_generato:
        logging.error("Fallimento nella generazione del piano: l'output dell'IA è vuoto o non contiene task azionabili.")
        update_business_plan_status(task_index, phase_index, "planning_failed")
        return
    # ------------------------------------

    plan_path = os.path.join(repo_root, 'development_plan.md')
    with open(plan_path, 'w') as f:
        f.write(piano_generato)
    logging.info(f"Piano di sviluppo TDD valido salvato in '{plan_path}'")

    update_business_plan_status(task_index, phase_index, "planned")
    commit_message = f"feat(project): Generato piano TDD valido per '{task_description[:45]}...'"
    commit_and_push_changes(repo_root, commit_message, "main")
    
    logging.info(f"--- ProjectBot: Pianificazione TDD completata. ---")