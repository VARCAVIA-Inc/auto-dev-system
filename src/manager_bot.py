import os
import yaml
import subprocess
import time
from github import Github
from src.utils.email_sender import send_email
from src.project_bot import run_project_bot, init_project_bot_env
from src.utils.git_utils import push_changes_to_main # Importa la funzione di push

def get_repo_root():
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

def main():
    print("Manager-Bot avviato.")
    # Inizializzazione delle credenziali
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    
    init_project_bot_env(OPENAI_API_KEY, RECEIVER_EMAIL, SENDER_EMAIL, GITHUB_TOKEN)

    # Leggi il Business Plan
    business_plan_path = 'src/business_plan.yaml'
    with open(business_plan_path, 'r') as file:
        business_plan = yaml.safe_load(file)
    
    repo_root = get_repo_root()

    # Logica decisionale principale
    for phase_index, phase in enumerate(business_plan.get('phases', [])):
        for task_index, task in enumerate(phase.get('tasks', [])):
            
            # CASO 1: Task nuovo, da pianificare
            if task.get('status') == 'pending' and task.get('agent') == 'ProjectBot':
                print(f"Trovato task PENDING: {task.get('description')}")
                run_project_bot(task, task_index, phase_index)
                print("Un task è stato pianificato. Termino per questa esecuzione.")
                return # Esci per riesaminare lo stato al prossimo run

            # --- NUOVA LOGICA PER LA FASE 2 ---
            # CASO 2: Task pianificato, da eseguire
            elif task.get('status') == 'planned':
                print(f"Trovato task PLANNED: {task.get('description')}. Inizio esecuzione delegata.")
                plan_path = os.path.join(repo_root, 'development_plan.md')
                
                try:
                    with open(plan_path, 'r+') as f:
                        lines = f.readlines()
                        
                        # Trova il primo sotto-task non completato
                        next_subtask_index = -1
                        for i, line in enumerate(lines):
                            if line.strip().startswith('- [ ]'):
                                next_subtask_index = i
                                break
                        
                        if next_subtask_index != -1:
                            # Estrai la descrizione del sotto-task
                            subtask_description = lines[next_subtask_index].replace('- [ ]', '').strip()
                            print(f"Delego il sotto-task: '{subtask_description}'")

                            # Prepara i parametri per l'Operator_Bot
                            branch_name = f"operator/task-{int(time.time())}"
                            commit_message = f"feat: Implementa '{subtask_description[:30]}...'"
                            
                            # Comando per avviare il workflow dell'Operator Bot
                            command = [
                                'gh', 'workflow', 'run', 'operator_bot_workflow.yml',
                                '-f', f'branch_name={branch_name}',
                                '-f', f'task_description={subtask_description}',
                                '-f', f'commit_message={commit_message}'
                            ]
                            
                            # Esegui il comando
                            subprocess.run(command, check=True)
                            print(f"Workflow 'Operator Bot' avviato per il branch '{branch_name}'.")

                            # Aggiorna il piano di sviluppo per segnare il task come "in corso"
                            lines[next_subtask_index] = lines[next_subtask_index].replace('[ ]', '[▶️] In Progress')
                            f.seek(0)
                            f.writelines(lines)
                            
                            # Committa l'aggiornamento del piano
                            push_changes_to_main(repo_root, f"chore: Avviato sotto-task '{subtask_description[:30]}...'")

                        else:
                            print("Tutti i sotto-task del piano sono completati. Aggiorno stato a 'completed'.")
                            # Qui aggiorneremo lo stato del task principale a 'completed'
                            # Per ora lo lasciamo in 'planned'
                            pass

                except FileNotFoundError:
                    print("Errore: development_plan.md non trovato per un task pianificato.")

                print("Un sotto-task è stato delegato. Termino per questa esecuzione.")
                return # Esci per riesaminare lo stato al prossimo run

    print("Nessun task attivo (pending o planned) trovato. In attesa.")

if __name__ == "__main__":
    main()
