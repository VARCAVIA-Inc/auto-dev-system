import os
import yaml
import subprocess
import time
import logging
from src.utils.logging_utils import setup_logging
from src.utils.git_utils import commit_and_push_changes
from src.bots.project_bot import run_project_bot

def get_repo_root():
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

def delegate_to_operator(task_line):
    """Attiva il workflow dell'OperatorBot per un singolo task."""
    task_description = task_line.replace("- [ ]", "").strip()
    timestamp = int(time.time())
    branch_name = f"autodev/task-{timestamp}"
    commit_message = f"feat: Implementa task '{task_description[:40]}...'"

    logging.info(f"Delega del task: '{task_description}' all'OperatorBot sul branch '{branch_name}'.")
    
    command = [
        'gh', 'workflow', 'run', 'operator_bot.yml',
        '-f', f'branch_name={branch_name}',
        '-f', f'task_description={task_description}',
        '-f', f'commit_message={commit_message}',
        '--ref', 'main'
    ]
    
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
    
    repo_root = get_repo_root()
    business_plan_path = os.path.join(repo_root, 'src', 'business_plan.yaml')
    
    try:
        with open(business_plan_path, 'r') as file:
            business_plan = yaml.safe_load(file)
    except FileNotFoundError:
        logging.critical(f"business_plan.yaml non trovato. Interruzione.")
        return

    for phase_index, phase in enumerate(business_plan.get('phases', [])):
        for task_index, task in enumerate(phase.get('tasks', [])):
            task_status = task.get('status')
            task_description = task.get('description')

            if task_status == 'pending':
                logging.info(f"Trovato task 'pending': '{task_description}'. Attivo il ProjectBot.")
                run_project_bot(task, task_index, phase_index)
                return

            elif task_status == 'planned':
                logging.info(f"Trovato task 'planned': '{task_description}'. Supervisione del piano.")
                plan_path = os.path.join(repo_root, 'development_plan.md')
                
                try:
                    with open(plan_path, 'r+') as f:
                        lines = f.readlines()
                        
                        for i, line in enumerate(lines):
                            if line.strip().startswith("- [ ]"):
                                if delegate_to_operator(line):
                                    lines[i] = line.replace("- [ ]", "- [x]", 1)
                                    f.seek(0)
                                    f.writelines(lines)
                                    f.truncate()
                                    commit_msg = f"chore(manager): Delegato task '{line.strip()[:40]}...'"
                                    commit_and_push_changes(repo_root, commit_msg, "main")
                                return
                        
                        logging.info(f"Tutti i sotto-task per '{task_description}' completati.")
                        task['status'] = 'completed'
                        with open(business_plan_path, 'w') as bp_file:
                            yaml.dump(business_plan, bp_file, default_flow_style=False, sort_keys=False)
                        
                        commit_msg_bp = f"feat(manager): Completa il task '{task_description[:50]}...'"
                        commit_and_push_changes(repo_root, commit_msg_bp, "main")
                        
                        os.remove(plan_path)
                        commit_msg_plan = "chore(manager): Rimuove il piano di sviluppo completato"
                        commit_and_push_changes(repo_root, commit_msg_plan, "main")
                        return
                            
                except FileNotFoundError:
                    logging.error(f"Piano di sviluppo non trovato per il task 'planned'.")
                    return

    logging.info("--- ManagerBot: Nessun task attivo trovato. Ciclo completato. ---")

if __name__ == "__main__":
    main()