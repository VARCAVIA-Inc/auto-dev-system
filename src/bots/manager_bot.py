import os
import yaml
import subprocess
import time
import logging
import json
import re
from src.utils.logging_utils import setup_logging
from src.utils.git_utils import commit_and_push_changes
from src.bots.project_bot import run_project_bot

# Regex per trovare e catturare i componenti di un task
TASK_REGEX = re.compile(r'(-\s*\[\s*\]\s*\[)(PENDING|IN_PROGRESS|FAILED|PR_OPEN|DONE)(\]:\s*\[.*\]\s*.*)')
STATUS_REGEX = re.compile(r'(-\s*\[\s*\]\s*\[)(PENDING|IN_PROGRESS|FAILED|PR_OPEN|DONE|.*)(\].*)')


def get_repo_root():
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

def update_task_status_in_plan(task_line, new_status, plan_path):
    """Aggiorna lo stato di un task specifico nel file development_plan.md."""
    logging.info(f"Tentativo di aggiornare il task '{task_line.strip()}' allo stato '{new_status}'")
    try:
        with open(plan_path, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        updated = False
        for line in lines:
            if line.strip() == task_line.strip():
                # Sostituisce solo lo stato, mantenendo il resto della riga
                new_line = STATUS_REGEX.sub(r'\g<1>' + new_status + r'\g<3>', line)
                new_lines.append(new_line)
                logging.info(f"Task aggiornato: {new_line.strip()}")
                updated = True
            else:
                new_lines.append(line)

        if updated:
            with open(plan_path, 'w') as f:
                f.writelines(new_lines)
            return True
    except Exception as e:
        logging.error(f"Errore durante l'aggiornamento del file di piano: {e}")
    return False


def manage_pull_requests(plan_path):
    """Gestisce le PR aperte, aggiornando lo stato dei task nel piano di sviluppo."""
    logging.info("--- ManagerBot: Inizio fase di gestione Pull Request ---")
    gh_command = ['gh', 'pr', 'list', '--head', 'autodev/', '--state', 'open', '--json', 'number,headRefName,title,status']
    
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

        logging.info(f"Trovate {len(prs)} Pull Request aperte dai bot.")
        with open(plan_path, 'r') as f:
            tasks = [line.strip() for line in f.readlines()]

        for pr in prs:
            pr_number, branch_name, title, status = pr['number'], pr['headRefName'], pr['title'], pr.get('status', 'PENDING').upper()
            logging.info(f"Analizzo PR #{pr_number} ('{title}') dal branch '{branch_name}' con stato CI '{status}'.")

            # Trova il task corrispondente basandosi sul titolo della PR/commit
            commit_prefix = "feat: Implementa task '"
            task_description_prefix = title.replace(commit_prefix, "").replace("...", "").strip()
            
            associated_task = None
            for task in tasks:
                if task_description_prefix in task:
                    associated_task = task
                    break
            
            if not associated_task:
                logging.warning(f"Nessun task associato trovato per la PR #{pr_number}. Salto.")
                continue

            if status == 'SUCCESS':
                logging.info(f"PR #{pr_number} ha superato i test. Attivo il merge automatico.")
                merge_command = ['gh', 'pr', 'merge', str(pr_number), '--auto', '--squash', '--delete-branch']
                subprocess.run(merge_command, check=True, capture_output=True, text=True)
                logging.info(f"✅ Merge per PR #{pr_number} attivato con successo.")
                if update_task_status_in_plan(associated_task, "DONE", plan_path):
                     commit_and_push_changes(get_repo_root(), f"chore(manager): Task completato e mergiato '{title[:40]}...'", "main")

            elif status == 'FAILURE':
                logging.warning(f"PR #{pr_number} ha fallito i test. La chiudo e segno il task come FAILED.")
                comment_body = "I controlli di validazione automatici (CI) sono falliti. Chiudo questa PR per permettere un nuovo tentativo. Il log del fallimento è disponibile nella tab 'Checks'."
                subprocess.run(['gh', 'pr', 'comment', str(pr_number), '--body', comment_body], check=True)
                subprocess.run(['gh', 'pr', 'close', str(pr_number)], check=True)
                # La delete-branch è gestita dal merge, qui la facciamo manualmente
                subprocess.run(['git', 'push', 'origin', '--delete', branch_name], check=False) # check=False perché potrebbe già essere stata cancellata
                if update_task_status_in_plan(associated_task, "FAILED", plan_path):
                     commit_and_push_changes(get_repo_root(), f"chore(manager): Task fallito e revertito '{title[:40]}...'", "main")

            else: # PENDING
                logging.info(f"PR #{pr_number} è in attesa dei controlli. Aggiorno lo stato del task a PR_OPEN.")
                if "[PR_OPEN]" not in associated_task:
                    if update_task_status_in_plan(associated_task, "PR_OPEN", plan_path):
                        commit_and_push_changes(get_repo_root(), f"chore(manager): PR aperta per task '{title[:40]}...'", "main")


    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        logging.error(f"Errore durante la gestione delle Pull Request: {e}", exc_info=True)


def delegate_to_operator(task_line, plan_path):
    # Estrae la descrizione pulita per il messaggio di commit
    clean_description = re.sub(r'-\s*\[\s*\]\s*\[.*?\]\s*\[.*?\]\s*', '', task_line).strip()
    timestamp = int(time.time())
    branch_name = f"autodev/task-{timestamp}"
    commit_message = f"feat: Implementa task '{clean_description[:40]}...'"
    
    logging.info(f"Delega del task: '{clean_description}' all'OperatorBot sul branch '{branch_name}'.")

    # Prima aggiorna lo stato a IN_PROGRESS e pusha
    if not update_task_status_in_plan(task_line, "IN_PROGRESS", plan_path):
        logging.error("Impossibile aggiornare lo stato del task a IN_PROGRESS. Annullamento delega.")
        return False
    
    commit_msg = f"chore(manager): Delega task '{clean_description[:40]}...'"
    commit_and_push_changes(get_repo_root(), commit_msg, "main")
    logging.info(f"Stato del task aggiornato a IN_PROGRESS e pushato su main.")

    # Ora lancia il workflow dell'operatore
    workflow_name = '2_operator_bot.yml'
    command = ['gh', 'workflow', 'run', workflow_name, '-f', f'branch_name={branch_name}', '-f', f'task_description={task_line}', '-f', f'commit_message={commit_message}', '--ref', 'main']
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        logging.info("✅ Workflow dell'OperatorBot attivato con successo.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Errore attivazione OperatorBot: {e.stderr}")
        # Se il workflow non parte, revertiamo lo stato a PENDING
        update_task_status_in_plan(task_line, "PENDING", plan_path)
        commit_and_push_changes(get_repo_root(), f"chore(manager): Revert delega fallita per '{clean_description[:40]}...'", "main")
        return False


def main():
    setup_logging()
    logging.info("--- ManagerBot: Avviato. Inizio nuovo ciclo di supervisione. ---")
    
    repo_root = get_repo_root()
    business_plan_path = os.path.join(repo_root, 'src', 'business_plan.yaml')
    plan_path = os.path.join(repo_root, 'development_plan.md')

    # Fase 1: Gestire lo stato corrente delle PR
    if os.path.exists(plan_path):
        manage_pull_requests(plan_path)

    # Fase 2: Controllare il piano di sviluppo e agire
    if os.path.exists(plan_path):
        logging.info("Trovato 'development_plan.md'. Supervisione del piano in corso...")
        with open(plan_path, 'r') as f:
            lines = f.readlines()
        
        all_done = True
        for line in lines:
            if not line.strip(): continue
            # Se anche un solo task non è DONE, il piano non è completo
            if "[DONE]" not in line:
                all_done = False
            # Trova il prossimo task da eseguire (PENDING o FAILED)
            if "[PENDING]" in line or "[FAILED]" in line:
                logging.info(f"Trovato task attivo: {line.strip()}")
                if delegate_to_operator(line, plan_path):
                    logging.info("Task delegato, in attesa del prossimo ciclo di supervisione.")
                else:
                    logging.error("Fallimento nella delega del task. Il problema verrà rianalizzato al prossimo ciclo.")
                return # Gestisci un solo task per ciclo per semplicità

        if all_done:
            logging.info("🎉 Tutti i sotto-task del piano di sviluppo sono completati!")
            # Qui si può implementare la logica per archiviare il piano e aggiornare il business_plan.yaml
            os.remove(plan_path)
            commit_msg_plan = "chore(manager): Rimuove il piano di sviluppo completato"
            commit_and_push_changes(repo_root, commit_msg_plan, "main")
            logging.info("Piano di sviluppo archiviato. In attesa di un nuovo task di business.")

    else:
        # Fase 3: Se non c'è un piano, crearne uno se necessario
        logging.info("Nessun 'development_plan.md' trovato. Controllo il 'business_plan.yaml' per task in attesa.")
        with open(business_plan_path, 'r') as file:
            business_plan = yaml.safe_load(file)
        
        for p_idx, phase in enumerate(business_plan.get('phases', [])):
            for t_idx, task in enumerate(phase.get('tasks', [])):
                if task.get('status') == 'pending':
                    logging.info(f"Trovato task di business 'pending': {task.get('description')}. Attivo il ProjectBot.")
                    run_project_bot(task, t_idx, p_idx)
                    return # Genera un solo piano alla volta

    logging.info("--- ManagerBot: Ciclo di supervisione completato. ---")

if __name__ == "__main__":
    main()