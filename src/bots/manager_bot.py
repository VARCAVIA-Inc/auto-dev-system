import os
import yaml
import subprocess
import time
import logging
import json
from src.utils.logging_utils import setup_logging
from src.utils.git_utils import commit_and_push_changes
from src.bots.project_bot import run_project_bot
from src.utils import state_utils # Importa il nostro nuovo sistema nervoso

def get_repo_root():
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

def manage_pull_requests():
    """
    Logica potenziata per la gestione completa delle Pull Request basata su etichette e stati.
    """
    logging.info("--- ManagerBot: Inizio fase di gestione Pull Request ---")
    
    gh_command = [
        'gh', 'pr', 'list',
        '--head', 'autodev/',
        '--state', 'open',
        '--json', 'number,headRefName,labels,status'
    ]
    
    try:
        result = subprocess.run(gh_command, capture_output=True, text=True)
        if result.returncode != 0 and (result.stdout.strip() == "" or "no open pull requests found" in result.stderr):
            logging.info("Nessuna Pull Request aperta trovata per i bot.")
            return
        result.check_returncode()
        prs = json.loads(result.stdout)
        if not prs:
            logging.info("Nessuna Pull Request aperta trovata per i bot.")
            return

        logging.info(f"Trovate {len(prs)} Pull Request create dai bot.")
        for pr in prs:
            pr_number = pr['number']
            branch_name = pr['headRefName']
            labels = [label['name'] for label in pr.get('labels', [])]
            ci_status = pr.get('status', 'PENDING').upper()

            logging.info(f"Analizzo PR #{pr_number} dal branch '{branch_name}' con stato CI '{ci_status}' e etichette {labels}.")

            if 'ci: passed' in labels:
                logging.info(f"PR #{pr_number} ha superato i test. Eseguo il merge.")
                merge_command = ['gh', 'pr', 'merge', str(pr_number), '--squash', '--delete-branch']
                subprocess.run(merge_command, check=True)
                logging.info(f"✅ Merge per PR #{pr_number} completato.")
            
            elif 'ci: failed' in labels or 'status: failed' in labels:
                 logging.warning(f"PR #{pr_number} ha fallito i test o l'esecuzione. Chiudo la PR.")
                 comment_body = "Questa PR ha fallito i controlli automatici o l'esecuzione del task. Verrà chiusa e il task sarà riprogrammato."
                 subprocess.run(['gh', 'pr', 'comment', str(pr_number), '--body', comment_body], check=True)
                 subprocess.run(['gh', 'pr', 'close', str(pr_number)], check=True)
                 subprocess.run(['gh', 'repo', 'delete-branch', branch_name], check=True)

    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        logging.error(f"Errore durante la gestione delle Pull Request: {e}", exc_info=True)

def delegate_to_operator(task: dict):
    """Attiva il workflow dell'OperatorBot passando l'indice della linea del task."""
    task_description = task['description']
    task_line_index = task['line_index']
    timestamp = int(time.time())
    branch_name = f"autodev/task-{timestamp}"
    
    logging.info(f"Delega del task (linea {task_line_index}): '{task_description}' all'OperatorBot.")
    
    workflow_name = '2_operator_bot.yml'
    command = [
        'gh', 'workflow', 'run', workflow_name,
        '-f', f'branch_name={branch_name}',
        '-f', f'task_description={task_description}',
        '-f', f'task_line_index={task_line_index}' # Passiamo l'indice
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        logging.info("✅ Workflow dell'OperatorBot attivato.")
        state_utils.update_task_status(task_line_index, "IN_PROGRESS")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Errore attivazione OperatorBot: {e.stderr}")
        state_utils.update_task_status(task_line_index, "FAILED")
        return False

def main():
    setup_logging()
    logging.info("--- ManagerBot: Avviato. Inizio ciclo di supervisione. ---")
    
    manage_pull_requests()

    repo_root = get_repo_root()
    business_plan_path = os.path.join(repo_root, 'src', 'business_plan.yaml')
    
    try:
        with open(business_plan_path, 'r') as file:
            business_plan = yaml.safe_load(file)
    except FileNotFoundError:
        logging.critical("business_plan.yaml non trovato. Interruzione.")
        return

    # Se un piano esiste, la priorità è eseguirlo
    if os.path.exists(state_utils.get_plan_path()):
        next_task = state_utils.find_next_task()
        if next_task:
            delegate_to_operator(next_task)
            # Non facciamo più il commit qui, lo stato è già gestito
        else:
            logging.info("Tutti i sotto-task del piano di sviluppo sono completati o in corso.")
            # ... (logica futura per marcare il task del business plan come 'completed')
    else:
        # Altrimenti, cerca un nuovo task da pianificare
        for p_idx, phase in enumerate(business_plan.get('phases', [])):
            for t_idx, task in enumerate(phase.get('tasks', [])):
                if task.get('status') == 'pending':
                    logging.info(f"Trovato task 'pending': {task.get('description')}. Attivo il ProjectBot.")
                    run_project_bot(task, t_idx, p_idx)
                    return

    logging.info("--- ManagerBot: Nessun task attivo o piano da eseguire. Ciclo completato. ---")

if __name__ == "__main__":
    main()