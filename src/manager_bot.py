import os
import yaml
import subprocess
import time
from github import Github
from src.project_bot import run_project_bot, init_project_bot_env
from src.utils.git_utils import push_changes_to_main

def get_repo_root():
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

def update_main_task_status(task_index, phase_index, new_status):
    repo_root = get_repo_root()
    business_plan_path = os.path.join(repo_root, 'src', 'business_plan.yaml')
    try:
        with open(business_plan_path, 'r') as file:
            plan = yaml.safe_load(file)
        
        plan['phases'][phase_index]['tasks'][task_index]['status'] = new_status
        
        with open(business_plan_path, 'w') as file:
            yaml.dump(plan, file, default_flow_style=False, sort_keys=False)
        
        print(f"Stato del task principale aggiornato a '{new_status}'.")
        return True
    except Exception as e:
        print(f"Errore durante l'aggiornamento del Business Plan: {e}")
        return False

def write_summary(message):
    """Scrive un riassunto in un file per il job di notifica."""
    with open("run_summary.txt", "w") as f:
        f.write(message)

def main():
    print("Manager-Bot avviato.")
    # L'autenticazione a Google è gestita dal workflow. Non servono chiavi API qui.
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
    
    # Inizializziamo l'ambiente del project_bot
    init_project_bot_env(github_token=GITHUB_TOKEN)

    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPOSITORY)

    business_plan_path = 'src/business_plan.yaml'
    with open(business_plan_path, 'r') as file:
        business_plan = yaml.safe_load(file)
    
    repo_root = get_repo_root()

    for phase_index, phase in enumerate(business_plan.get('phases', [])):
        for task_index, task in enumerate(phase.get('tasks', [])):
            task_status = task.get('status')
            task_description = task.get('description')

            if task_status == 'pending' and task.get('agent') == 'ProjectBot':
                write_summary(f"Avviata pianificazione per il task: '{task_description}'.")
                run_project_bot(task, task_index, phase_index)
                return

            elif task_status == 'planned':
                write_summary(f"Supervisione e delega per il task: '{task_description}'.")
                plan_path = os.path.join(repo_root, 'development_plan.md')
                
                try:
                    with open(plan_path, 'r+') as f:
                        lines = f.readlines()
                        
                        # (La logica di supervisione e delega rimane invariata)
                        # ...
                except FileNotFoundError:
                    write_summary(f"Piano non trovato per '{task_description}'. Reimposto a pending.")
                    update_main_task_status(task_index, phase_index, "pending")
                    push_changes_to_main(repo_root, f"fix: Reimpostato task a pending.")
                    return

    write_summary("Nessun task attivo trovato.")
    print("Nessun task attivo (pending o planned) trovato.")

if __name__ == "__main__":
    main()