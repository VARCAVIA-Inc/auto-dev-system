import os
import yaml
import subprocess
import time
import logging
from src.utils.git_utils import push_changes_to_branch
from src.utils.logging_utils import setup_logging
from src.project_bot import run_project_bot # Manteniamo l'import diretto

def get_repo_root():
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

def write_summary(message):
    with open("run_summary.txt", "w") as f:
        f.write(message)

def delegate_to_operator(task_line, main_task_description):
    repo_slug = os.getenv("GITHUB_REPOSITORY")
    if not repo_slug:
        logging.error("Errore: GITHUB_REPOSITORY non trovato.")
        return False
        
    task_description = task_line.replace("- [ ]", "").strip()
    
    timestamp = int(time.time())
    branch_name = f"autodev/task-{timestamp}"
    commit_message = f"feat: Implementa task '{task_description[:40]}...'"

    logging.info(f"Delego il task: '{task_description}' all'Operator Bot sul branch '{branch_name}'.")
    
    command = [
        'gh', 'workflow', 'run', 'operator_bot_workflow.yml',
        '-f', f'branch_name={branch_name}',
        '-f', f'task_description={task_description}',
        '-f', f'commit_message={commit_message}',
        '--ref', 'main'
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        logging.info("✅ Workflow dell'Operator Bot attivato con successo.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Errore durante l'attivazione del workflow dell'Operator Bot: {e.stderr}")
        return False

def main():
    setup_logging()
    logging.info("--- ManagerBot: Avviato. Inizio supervisione del Business Plan. ---")
    
    repo_root = get_repo_root()
    business_plan_path = os.path.join(repo_root, 'src', 'business_plan.yaml')
    
    try:
        with open(business_plan_path, 'r') as file:
            business_plan = yaml.safe_load(file)
    except FileNotFoundError:
        logging.critical(f"File business_plan.yaml non trovato in '{business_plan_path}'. Interruzione.")
        write_summary("ERRORE: business_plan.yaml non trovato.")
        return

    for phase_index, phase in enumerate(business_plan.get('phases', [])):
        for task_index, task in enumerate(phase.get('tasks', [])):
            task_status = task.get('status')
            task_description = task.get('description')

            if task_status == 'pending':
                logging.info(f"Trovato task 'pending': '{task_description}'. Avvio del ProjectBot.")
                write_summary(f"Avviata pianificazione per il task: '{task_description}'.")
                run_project_bot(task, task_index, phase_index)
                return # Esegue un solo task per run

            elif task_status == 'planned':
                logging.info(f"Trovato task 'planned': '{task_description}'. Supervisione e delega.")
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
                                
                                commit_msg = f"chore(manager): Delegato task '{pending_sub_task_line.strip()[:40]}...'"
                                push_changes_to_branch(repo_root, commit_msg, "main")
                                write_summary(f"Delegato sotto-task all'Operator Bot. In attesa di PR.")
                            else:
                                write_summary("Fallimento nella delega del sotto-task.")
                            return # Esegue una sola delega per run
                        
                        else:
                            logging.info(f"Tutti i sotto-task per '{task_description}' sono completati.")
                            task['status'] = 'completed'
                            with open(business_plan_path, 'w') as bp_file:
                                yaml.dump(business_plan, bp_file, default_flow_style=False, sort_keys=False)
                            
                            commit_msg_bp = f"feat(manager): Completato task '{task_description[:50]}...'"
                            push_changes_to_branch(repo_root, commit_msg_bp, "main")
                            
                            os.remove(plan_path)
                            commit_msg_plan = "chore(manager): Rimosso piano di sviluppo completato"
                            push_changes_to_branch(repo_root, commit_msg_plan, "main")
                            
                            write_summary(f"Task '{task_description}' completato con successo.")
                            return # Esegue un solo completamento per run
                            
                except FileNotFoundError:
                    logging.error(f"Piano di sviluppo non trovato per il task 'planned': '{task_description}'.")
                    write_summary(f"ERRORE: development_plan.md non trovato per un task pianificato.")
                    return

    logging.info("Nessun task attivo (pending o planned) trovato nel business plan. In attesa del prossimo ciclo.")
    write_summary("Nessun task attivo (pending o planned) trovato nel business plan.")

if __name__ == "__main__":
    main()