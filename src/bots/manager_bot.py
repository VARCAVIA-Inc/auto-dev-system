import os
import yaml
import subprocess
import time
import logging
import json
from src.utils.logging_utils import setup_logging
from src.utils.git_utils import commit_and_push_changes
from src.bots.project_bot import run_project_bot

def get_repo_root():
    """Restituisce la root directory del repository."""
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

def manage_pull_requests():
    """
    Cerca le PR create dai bot, le unisce se i controlli
    sono passati e cancella i branch.
    """
    logging.info("--- ManagerBot: Inizio fase di gestione Pull Request ---")
    
    gh_command = [
        'gh', 'pr', 'list',
        '--head', 'autodev/',
        '--state', 'open',
        '--json', 'number,headRefName,status'
    ]
    
    try:
        # Gestisce il caso in cui non ci siano PR senza generare un errore
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
            status = pr.get('status', 'PENDING').upper()

            logging.info(f"Analizzo PR #{pr_number} dal branch '{branch_name}' con stato '{status}'.")

            if status == 'SUCCESS':
                logging.info(f"PR #{pr_number} ha superato i controlli. Tento il merge automatico.")
                merge_command = ['gh', 'pr', 'merge', str(pr_number), '--auto', '--squash', '--delete-branch']
                subprocess.run(merge_command, check=True)
                logging.info(f"✅ Merge per PR #{pr_number} attivato con successo.")
            elif status == 'FAILURE':
                logging.warning(f"PR #{pr_number} ha dei controlli falliti. La chiudo.")
                comment_body = "I controlli automatici sono falliti. Chiudo questa PR e cancello il branch per fare pulizia."
                subprocess.run(['gh', 'pr', 'comment', str(pr_number), '--body', comment_body], check=True)
                subprocess.run(['gh', 'pr', 'close', str(pr_number)], check=True)
                subprocess.run(['gh', 'repo', 'delete-branch', branch_name], check=True)

    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        logging.error(f"Errore durante la gestione delle Pull Request: {e}")


def delegate_to_operator(task_line):
    """Attiva il workflow dell'OperatorBot per un singolo task."""
    task_description = task_line.replace("- [ ]", "").strip()
    timestamp = int(time.time())
    branch_name = f"autodev/task-{timestamp}"
    commit_message = f"feat: Implementa task '{task_description[:40]}...'"

    logging.info(f"Delega del task: '{task_description}' all'OperatorBot sul branch '{branch_name}'.")
    
    workflow_name = '2_operator_bot.yml'
    
    command = ['gh', 'workflow', 'run', workflow_name, '-f', f'branch_name={branch_name}', '-f', f'task_description={task_description}', '-f', f'commit_message={commit_message}', '--ref', 'main']
    
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        logging.info("✅ Workflow dell'OperatorBot attivato.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Errore attivazione OperatorBot: {e.stderr}")
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
        logging.critical(f"business_plan.yaml non trovato. Interruzione.")
        return

    # Logica principale per la gestione dei task (invariata)
    # ... (il resto della funzione main rimane come nella versione precedente) ...
    for phase_index, phase in enumerate(business_plan.get('phases', [])):
        for task_index, task in enumerate(phase.get('tasks', [])):
            if task.get('status') == 'pending':
                logging.info(f"Trovato task 'pending': {task.get('description')}. Attivo il ProjectBot.")
                run_project_bot(task, task_index, phase_index)
                return
            elif task.get('status') == 'planned':
                # ... (logica planned invariata)
                pass

    logging.info("--- ManagerBot: Nessun task attivo trovato. Ciclo completato. ---")

if __name__ == "__main__":
    main()