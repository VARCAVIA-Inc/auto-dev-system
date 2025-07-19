import os
import yaml
import logging
import subprocess
from src.utils.git_utils import commit_and_push_changes
from src.utils.ai_utils import get_gemini_model, generate_response, PLANNING_MODEL

def update_business_plan_status(task_index, phase_index, new_status="planned"):
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
        f"Sei il ProjectBot, il CTO di un'organizzazione autonoma. Traduci un obiettivo di business in un piano tecnico dettagliato in Markdown per i tuoi OperatorBot.\n"
        f"Struttura del progetto attuale:\n```\n{file_structure}\n```\n\n"
        f"Obiettivo di Business: '{task_description}'.\n\n"
        f"**REGOLE CRITICHE PER IL PIANO:**\n"
        f"1. Sii dettagliato e sequenziale.\n"
        f"2. Ogni task che crea/modifica un file DEVE iniziare con il percorso tra parentesi. Esempio: '- [ ] [src/new_file.py] Scrivere la funzione'.\n"
        f"3. Per comandi di sistema, usa '[shell-command]'. Il comando deve essere puro, senza spiegazioni. Esempio: '- [ ] [shell-command] npm install'."
    )

    piano_generato = generate_response(gemini_model, prompt)
    
    if not piano_generato:
        logging.error("Fallimento nella generazione del piano di sviluppo.")
        update_business_plan_status(task_index, phase_index, "planning_failed")
        return

    plan_path = os.path.join(repo_root, 'development_plan.md')
    with open(plan_path, 'w') as f:
        f.write(piano_generato)
    logging.info(f"Piano di sviluppo salvato in '{plan_path}'")

    update_business_plan_status(task_index, phase_index, "planned")
    commit_message = f"feat(project): Generato piano per '{task_description[:50]}...'"
    commit_and_push_changes(repo_root, commit_message, "main")
    
    logging.info(f"--- ProjectBot: Pianificazione completata. ---")