import os
import yaml
import subprocess
import time
from src.project_bot import run_project_bot, init_project_bot_env
from src.utils.git_utils import push_changes_to_main

def get_repo_root():
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

def update_main_task_status(task_index, phase_index, new_status):
    """
    Funzione di utility per aggiornare lo stato nel business_plan.yaml.
    """
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


def main():
    print("Manager-Bot avviato.")
    # Inizializzazione
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    init_project_bot_env(OPENAI_API_KEY, None, None, GITHUB_TOKEN)

    business_plan_path = 'src/business_plan.yaml'
    with open(business_plan_path, 'r') as file:
        business_plan = yaml.safe_load(file)
    
    repo_root = get_repo_root()

    # Logica decisionale principale
    for phase_index, phase in enumerate(business_plan.get('phases', [])):
        for task_index, task in enumerate(phase.get('tasks', [])):
            
            task_status = task.get('status')
            task_description = task.get('description')

            # CASO 1: Task nuovo, da pianificare
            if task_status == 'pending' and task.get('agent') == 'ProjectBot':
                print(f"Trovato task PENDING: {task_description}")
                run_project_bot(task, task_index, phase_index)
                print("Un task è stato pianificato. Termino per questa esecuzione.")
                return

            # CASO 2: Task pianificato, da eseguire
            elif task_status == 'planned':
                print(f"Trovato task PLANNED: {task_description}. Controllo il piano di sviluppo.")
                plan_path = os.path.join(repo_root, 'development_plan.md')
                
                try:
                    with open(plan_path, 'r+') as f:
                        lines = f.readlines()
                        
                        next_subtask_index = -1
                        for i, line in enumerate(lines):
                            if line.strip().startswith('- [ ]'):
                                next_subtask_index = i
                                break
                        
                        # Se c'è un sotto-task da eseguire...
                        if next_subtask_index != -1:
                            subtask_description = lines[next_subtask_index].replace('- [ ]', '').strip()
                            print(f"Delego il sotto-task: '{subtask_description}'")

                            branch_name = f"operator/task-{int(time.time())}"
                            commit_message = f"feat: Implementa '{subtask_description[:30]}...'"
                            
                            command = [
                                'gh', 'workflow', 'run', 'operator_bot_workflow.yml',
                                '-f', f'branch_name={branch_name}',
                                '-f', f'task_description={subtask_description}',
                                '-f', f'commit_message={commit_message}'
                            ]
                            
                            subprocess.run(command, check=True, env=os.environ)
                            print(f"Workflow 'Operator Bot' avviato per il branch '{branch_name}'.")

                            lines[next_subtask_index] = lines[next_subtask_index].replace('[ ]', '[▶️] In Progress')
                            f.seek(0)
                            f.truncate()
                            f.writelines(lines)
                            
                            push_changes_to_main(repo_root, f"chore: Avviato sotto-task '{subtask_description[:30]}...'")
                            print("Un sotto-task è stato delegato. Termino per questa esecuzione.")
                            return
                        
                        # --- NUOVA LOGICA DI COMPLETAMENTO ---
                        # Se non ci sono più sotto-task '[ ]'...
                        else:
                            print("Tutti i sotto-task del piano sono stati delegati. Il progetto è considerato completo.")
                            
                            # Aggiorna lo stato del task principale a 'completed'
                            update_main_task_status(task_index, phase_index, "completed")
                            
                            # Rimuovi il piano di sviluppo ormai inutile
                            os.remove(plan_path)
                            print("File development_plan.md rimosso.")

                            # Committa lo stato finale
                            push_changes_to_main(repo_root, f"feat: Completato task principale '{task_description[:30]}...'")
                            print("Ciclo di sviluppo per questo task completato con successo.")
                            return

                except FileNotFoundError:
                    print(f"Errore: development_plan.md non trovato per il task pianificato '{task_description}'. Reimposto a 'pending'.")
                    update_main_task_status(task_index, phase_index, "pending")
                    push_changes_to_main(repo_root, f"fix: Reimpostato task '{task_description[:30]}...' a pending per rigenerare il piano.")
                    return

    print("Nessun task attivo (pending o planned) trovato. In attesa.")


if __name__ == "__main__":
    main()
