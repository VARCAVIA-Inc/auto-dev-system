# src/manager_bot.py
import os
import yaml
import subprocess
import time
from github import Github
from src.project_bot import run_project_bot, init_project_bot_env
from src.utils.git_utils import push_changes_to_main

def get_repo_root():
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

def write_summary(message):
    with open("run_summary.txt", "w") as f:
        f.write(message)

def delegate_to_operator(task_line, main_task_description):
    repo_slug = os.getenv("GITHUB_REPOSITORY")
    if not repo_slug:
        print("Errore: GITHUB_REPOSITORY non trovato.")
        return False
        
    task_description = task_line.replace("- [ ]", "").strip()
    
    timestamp = int(time.time())
    branch_name = f"autodev-task-{timestamp}"
    commit_message = f"feat: {task_description[:50]}"

    print(f"Delego il task: '{task_description}' all'Operator Bot.")
    print(f"Nuovo branch: {branch_name}")
    
    # MODIFICA: Il comando non passa più la chiave API
    command = [
        'gh', 'workflow', 'run', 'operator_bot_workflow.yml',
        '-f', f'branch_name={branch_name}',
        '-f', f'task_description={task_description}',
        '-f', f'commit_message={commit_message}',
        '--ref', 'main'
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print("Workflow dell'Operator Bot attivato con successo.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Errore durante l'attivazione del workflow dell'Operator Bot: {e.stderr}")
        return False

def main():
    print("Manager-Bot avviato.")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
    
    if not GITHUB_TOKEN or not GITHUB_REPOSITORY:
        print("Errore: Variabili d'ambiente GITHUB_TOKEN o GITHUB_REPOSITORY non trovate.")
        return

    init_project_bot_env(github_token=GITHUB_TOKEN)
    
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
                write_summary(f"Supervisione e delega per il task pianificato: '{task_description}'.")
                plan_path = os.path.join(repo_root, 'development_plan.md')
                
                try:
                    with open(plan_path, 'r+') as f:
                        lines = f.readlines()
                        
                        pending_sub_task_line = None
                        pending_sub_task_index = -1

                        for i, line in enumerate(lines):
                            if line.strip().startswith("- [ ]"):
                                pending_sub_task_line = line
                                pending_sub_task_index = i
                                break
                        
                        if pending_sub_task_line:
                            if delegate_to_operator(pending_sub_task_line, task_description):
                                lines[pending_sub_task_index] = pending_sub_task_line.replace("- [ ]", "- [x]", 1)
                                f.seek(0)
                                f.writelines(lines)
                                f.truncate()
                                
                                commit_msg = f"chore: Delegato task '{pending_sub_task_line.strip()}' all'operatore"
                                push_changes_to_main(repo_root, commit_msg)
                                write_summary(f"Delegato sotto-task all'Operator Bot. In attesa di PR.")
                            else:
                                write_summary("Fallimento nella delega del sotto-task.")
                            return
                        
                        else:
                            print(f"Tutti i sotto-task per '{task_description}' sono completati.")
                            task['status'] = 'completed'
                            with open(business_plan_path, 'w') as bp_file:
                                yaml.dump(business_plan, bp_file, default_flow_style=False, sort_keys=False)
                            
                            commit_msg = f"feat: Completato task '{task_description}'"
                            push_changes_to_main(repo_root, commit_msg)
                            os.remove(plan_path)
                            push_changes_to_main(repo_root, "chore: Rimosso piano di sviluppo completato")
                            write_summary(f"Task '{task_description}' completato con successo.")
                            return
                            
                except FileNotFoundError:
                    write_summary(f"Piano di sviluppo non trovato per '{task_description}'.")
                    return

    write_summary("Nessun task attivo (pending o planned) trovato nel business plan.")
    print("Nessun task attivo (pending o planned) trovato.")

if __name__ == "__main__":
    main()