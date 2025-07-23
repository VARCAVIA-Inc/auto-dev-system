import os
import yaml
import logging
import subprocess
import re
from src.utils.git_utils import commit_and_push_changes
from src.utils.ai_utils import get_gemini_model, generate_response, PLANNING_MODEL

def is_plan_valid(plan_text: str) -> bool:
    """Controlla se un piano di sviluppo generato è valido e usa il nuovo formato di stato."""
    logging.info("Validazione del piano di sviluppo generato...")
    has_tasks = False
    # Regex per validare il formato: '- [ ] [STATO] [target] descrizione'
    task_regex = re.compile(r'^\s*-\s*\[\s*\]\s*\[(PENDING|SHELL|TEST)\]\s*\[(.*?)\]\s*.*')
    
    for line in plan_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("- [ ]"):
            has_tasks = True
            if not task_regex.match(line):
                logging.error(f"Riga di task non valida trovata: '{line}'. Formato richiesto: '- [ ] [STATO] [target] ...'")
                return False
                
    if not has_tasks:
        logging.error("Validazione fallita: il piano non contiene task azionabili ('- [ ]').")
    
    return has_tasks

def update_business_plan_status(task_index, phase_index, new_status):
    repo_root = os.getenv('GITHUB_WORKSPACE', os.getcwd())
    business_plan_path = os.path.join(repo_root, 'src', 'business_plan.yaml')
    try:
        with open(business_plan_path, 'r') as file:
            plan = yaml.safe_load(file)
        plan['phases'][phase_index]['tasks'][task_index]['status'] = new_status
        with open(business_plan_path, 'w') as file:
            yaml.dump(plan, file, default_flow_style=False, sort_keys=False)
        logging.info(f"Stato del task nel Business Plan aggiornato a '{new_status}'.")
    except Exception as e:
        logging.error(f"Errore durante l'aggiornamento del Business Plan: {e}", exc_info=True)

def run_project_bot(task_details, task_index, phase_index):
    task_description = task_details.get('description', 'N/A')
    logging.info(f"--- ProjectBot: Inizio Pianificazione per '{task_description}' ---")
    
    try:
        gemini_model = get_gemini_model(PLANNING_MODEL)
        repo_root = os.getenv('GITHUB_WORKSPACE', os.getcwd())
        result = subprocess.run(['ls', '-R'], cwd=repo_root, capture_output=True, text=True, check=True)
        file_structure = result.stdout
    except Exception as e:
        logging.error(f"Errore nella preparazione della pianificazione: {e}")
        update_business_plan_status(task_index, phase_index, "planning_failed")
        return

    prompt = (
        f"Sei il ProjectBot, il CTO di un sistema di sviluppo autonomo. Il tuo compito è tradurre un obiettivo di business in un piano tecnico dettagliato e TDD (Test-Driven Development) in formato Markdown.\n"
        f"Struttura del progetto attuale:\n```\n{file_structure}\n```\n\n"
        f"Obiettivo di Business da pianificare: '{task_description}'.\n\n"
        f"**REGOLE CRITICHE E OBBLIGATORIE PER IL PIANO:**\n"
        f"1.  Il piano DEVE essere una lista di sotto-task in Markdown.\n"
        f"2.  Ogni sotto-task DEVE iniziare con '- [ ]' seguito da un marcatore di stato e un marcatore di target.\n"
        f"3.  Il formato esatto è: `- [ ] [STATO] [target] Descrizione chiara e atomica del task.`\n"
        f"4.  Il primo stato per ogni nuovo task DEVE essere `[PENDING]`.\n"
        f"5.  Il target può essere un percorso file (es. `[src/nuova_funzione.py]`) o un comando shell (`[shell-command]`).\n"
        f"6.  **APPROCCIO TDD OBBLIGATORIO**: Per ogni file di codice sorgente che crei o modifichi, DEVI prima creare un task per il file di test corrispondente. Esempio:\n"
        f"    - [ ] [PENDING] [tests/test_nuova_funzione.py] Scrivi test per la funzione 'calcola_risultato' che verifichi i casi X, Y, Z.\n"
        f"    - [ ] [PENDING] [src/nuova_funzione.py] Implementa la funzione 'calcola_risultato' che passi i test definiti.\n"
        f"7.  I comandi shell in '[shell-command]' devono essere puliti, senza apici inversi (backticks).\n\n"
        f"Ora, genera il piano di sviluppo TDD per l'obiettivo specificato."
    )

    piano_generato = generate_response(gemini_model, prompt)
    
    if not piano_generato or not is_plan_valid(piano_generato):
        logging.error("Fallimento nella generazione del piano: l'output dell'IA è vuoto o non rispetta il formato TDD richiesto.")
        update_business_plan_status(task_index, phase_index, "planning_failed")
        return

    plan_path = os.path.join(repo_root, 'development_plan.md')
    with open(plan_path, 'w') as f:
        f.write(piano_generato)
    logging.info(f"Piano di sviluppo TDD valido e state-aware salvato in '{plan_path}'")

    update_business_plan_status(task_index, phase_index, "planned")
    commit_message = f"feat(project): Generato piano TDD per '{task_description[:45]}...'"
    commit_and_push_changes(repo_root, commit_message, "main")
    
    logging.info(f"--- ProjectBot: Pianificazione TDD completata con successo. ---")