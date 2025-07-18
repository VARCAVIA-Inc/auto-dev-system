import os
import yaml
import logging
import subprocess
from src.utils.git_utils import push_changes_to_branch
from src.utils.logging_utils import setup_logging
from src.utils.ai_utils import get_gemini_model, generate_response, PLANNING_MODEL

def get_repo_root():
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

def update_business_plan_status(task_index, phase_index, new_status="planned"):
    repo_root = get_repo_root()
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
    setup_logging()
    task_description = task_details.get('description', 'N/A')
    logging.info(f"--- ProjectBot: Inizio Pianificazione per '{task_description}' ---")

    try:
        gemini_model = get_gemini_model(PLANNING_MODEL)
    except Exception as e:
        logging.critical(f"Impossibile inizializzare il modello AI. Interruzione. Errore: {e}")
        update_business_plan_status(task_index, phase_index, "planning_failed")
        return

    repo_root = get_repo_root()
    try:
        result = subprocess.run(['ls', '-R'], cwd=repo_root, capture_output=True, text=True, check=True)
        file_structure = result.stdout
    except Exception as e:
        file_structure = f"Impossibile leggere la struttura dei file: {e}"
        logging.warning(file_structure)

    prompt_per_piano = (
        f"Considerando la seguente struttura di file e cartelle già esistente nel progetto:\n"
        f"```\n{file_structure}\n```\n\n"
        f"Sei il ProjectBot, il CTO di un'organizzazione autonoma. Il tuo compito è tradurre un obiettivo di business in un piano tecnico dettagliato in Markdown per i tuoi OperatorBot.\n"
        f"Obiettivo di Business: '{task_description}'.\n"
        f"**REGOLE FONDAMENTALI PER IL PIANO:**\n"
        f"1. Sii dettagliato e sequenziale. Pensa passo dopo passo.\n"
        f"2. **NON** creare file o cartelle che esistono già.\n"
        f"3. Ogni sotto-task che modifica o crea un file DEVE iniziare con il percorso del file tra parentesi quadre. Esempio: '- [ ] [src/calculator.py] Definire la classe Calculator'.\n"
        f"4. Se un task è un'azione generica (installare dipendenze, creare cartelle), usa '[shell-command]'.\n"
        f"5. **REGOLA CRITICA**: Per i task di tipo '[shell-command]', il testo che segue DEVE essere **SOLO ED ESCLUSIVAMENTE** il comando puro, valido ed eseguibile. NON includere commenti, spiegazioni o backtick. Esempio CORRETTO: '- [ ] [shell-command] mkdir -p docs'. Esempio ERRATO: '- [ ] [shell-command] `mkdir docs` (crea la cartella)'."
    )

    piano_generato = generate_response(gemini_model, prompt_per_piano)
    
    if not piano_generato:
        logging.error("Fallimento nella generazione del piano di sviluppo.")
        update_business_plan_status(task_index, phase_index, "planning_failed")
        return

    logging.info("Piano di sviluppo generato con successo.")
    plan_path = os.path.join(repo_root, 'development_plan.md')
    try:
        with open(plan_path, 'w') as f:
            f.write(piano_generato)
        logging.info(f"Piano di sviluppo salvato in '{plan_path}'")
    except Exception as e:
        logging.error(f"Impossibile salvare il piano di sviluppo: {e}", exc_info=True)
        return

    update_business_plan_status(task_index, phase_index, "planned")
    commit_message = f"feat(project): Generato piano di sviluppo per '{task_description[:50]}...'"
    push_changes_to_branch(repo_root, commit_message, "main")
    
    logging.info(f"--- ProjectBot: Pianificazione per '{task_description}' completata. ---")