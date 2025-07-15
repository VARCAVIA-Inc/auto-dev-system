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

def main():
    print("Manager-Bot avviato.")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
    
    init_project_bot_env(OPENAI_API_KEY, None, None, GITHUB_TOKEN)

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
                print(f"Trovato task PENDING: {task_description}")
                run_project_bot(task, task_index, phase_index)
                return

            elif task_status == 'planned':
                print(f"Trovato task PLANNED: {task_description}. Avvio supervisione e delega.")
                plan_path = os.path.join(repo_root, 'development_plan.md')
                plan_changed = False
                
                try:
                    with open(plan_path, 'r+') as f:
                        lines = f.readlines()
                        
                        pull_requests = repo.get_pulls(state='all', head='operator/')
                        for pr in pull_requests:
                            if pr.is_merged():
                                pr_title = pr.title
                                if pr_title.startswith("feat: Implementa '"):
                                    subtask_key = pr_title.replace("feat: Implementa '", "").replace("...'", "")
                                    for i, line in enumerate(lines):
                                        if subtask_key in line and '[▶️]' in line:
                                            lines[i] = line.replace('[▶️] In Progress', '[✅] Fatto!')
                                            plan_changed = True
                                            print(f"Sotto-task '{subtask_key}' completato (PR unita).")
                                            break
                        if plan_changed:
                            f.seek(0)
                            f.truncate()
                            f.writelines(lines)
                            push_changes_to_main(repo_root, f"chore: Aggiorna piano, task completati")

                        next_subtask_index = -1
                        for i, line in enumerate(lines):
                            if line.strip().startswith('- [ ]'):
                                next_subtask_index = i
                                break
                        
                        if next_subtask_index != -1:
                            subtask_description = lines[next_subtask_index].replace('- [ ]', '').strip()
                            print(f"Delego il sotto-task: '{subtask_description}'")
                            branch_name = f"operator/task-{int(time.time())}"
                            commit_message = f"feat: Implementa '{subtask_description[:30]}...'"
                            
                            env = os.environ.copy()
                            env['GH_TOKEN'] = GITHUB_TOKEN
                            command = ['gh', 'workflow', 'run', 'operator_bot_workflow.yml', '-f', f'branch_name={branch_name}', '-f', f'task_description={subtask_description}', '-f', f'commit_message={commit_message}']
                            
                            subprocess.run(command, check=True, env=env)
                            print(f"Workflow 'Operator Bot' avviato per il branch '{branch_name}'.")

                            lines[next_subtask_index] = lines[next_subtask_index].replace('[ ]', '[▶️] In Progress')
                            f.seek(0)
                            f.truncate()
                            f.writelines(lines)
                            push_changes_to_main(repo_root, f"chore: Avviato sotto-task '{subtask_description[:30]}...'")
                            return

                        else:
                            all_done = all('[✅]' in line for line in lines if line.strip().startswith('- ['))
                            if all_done:
                                print("Tutti i sotto-task del piano sono completati. Chiudo il task principale.")
                                update_main_task_status(task_index, phase_index, "completed")
                                os.remove(plan_path)
                                push_changes_to_main(repo_root, f"feat: Completato task principale '{task_description[:30]}...'")
                                return
                
                except FileNotFoundError:
                    print(f"Errore: development_plan.md non trovato per un task pianificato. Reimposto a 'pending'.")
                    update_main_task_status(task_index, phase_index, "pending")
                    push_changes_to_main(repo_root, f"fix: Reimpostato task '{task_description[:30]}...' a pending.")
                    return

    print("Nessun task attivo (pending o planned) trovato. In attesa.")

if __name__ == "__main__":
    main()