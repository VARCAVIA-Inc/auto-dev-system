import os
import yaml
import subprocess
import time
import logging
import json
from src.utils.logging_utils import setup_logging
from src.utils.git_utils import commit_and_push_changes
from src.bots.project_bot import run_project_bot

# ... (funzioni manage_pull_requests e delegate_to_operator invariate) ...

def main():
    setup_logging()
    logging.info("--- ManagerBot: Avviato. Inizio ciclo di supervisione. ---")
    
    manage_pull_requests()

    repo_root = os.getenv('GITHUB_WORKSPACE', os.getcwd())
    business_plan_path = os.path.join(repo_root, 'src', 'business_plan.yaml')
    plan_path = os.path.join(repo_root, 'development_plan.md')

    try:
        with open(business_plan_path, 'r') as file:
            business_plan = yaml.safe_load(file)
    except FileNotFoundError:
        logging.critical(f"business_plan.yaml non trovato. Interruzione.")
        return

    # --- NUOVA LOGICA DI CONTROLLO STATO ---
    # 1. Se esiste un piano di sviluppo, la priorità è eseguirlo.
    if os.path.exists(plan_path):
        logging.info("Trovato un 'development_plan.md' esistente. Supervisione del piano in corso...")
        
        # Trova il task 'planned' corrispondente (assumiamo ce ne sia solo uno)
        planned_task = None
        for phase in business_plan.get('phases', []):
            for task in phase.get('tasks', []):
                if task.get('status') == 'planned':
                    planned_task = task
                    break
            if planned_task:
                break
        
        if not planned_task:
            logging.warning("Trovato 'development_plan.md' ma nessun task 'planned' nel business plan. Pulisco.")
            os.remove(plan_path)
            commit_and_push_changes(repo_root, "chore(manager): Rimosso piano di sviluppo orfano", "main")
            return

        # ... (la logica di delega esistente va qui) ...
        # (trova '- [ ]', delega, segna '- [x]', etc.)
        return

    # 2. Se non ci sono piani, cerca un nuovo task da pianificare.
    for phase_index, phase in enumerate(business_plan.get('phases', [])):
        for task_index, task in enumerate(phase.get('tasks', [])):
            if task.get('status') == 'pending':
                logging.info(f"Trovato task 'pending': {task.get('description')}. Attivo il ProjectBot.")
                run_project_bot(task, task_index, phase_index)
                return

    logging.info("--- ManagerBot: Nessun task attivo o piano da eseguire. Ciclo completato. ---")

if __name__ == "__main__":
    main()