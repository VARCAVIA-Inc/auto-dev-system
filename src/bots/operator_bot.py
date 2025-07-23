import os
import logging
import re
import subprocess
from git import Repo
from src.utils.logging_utils import setup_logging
from src.utils.ai_utils import get_gemini_model, generate_response, EXECUTION_MODEL
from src.utils import state_utils # Importa il nostro nuovo sistema nervoso

def create_pull_request(branch_name: str, task_status: str, error_log: str = ""):
    """Crea una Pull Request usando la CLI di GitHub, aggiungendo etichette di stato."""
    try:
        logging.info(f"Creazione della Pull Request per il branch '{branch_name}'...")
        env = os.environ.copy()
        env['GH_TOKEN'] = os.getenv("GITHUB_TOKEN")
        
        pr_title = f"feat: Esecuzione task del OperatorBot ({branch_name})"
        pr_body = f"Task completato dall'OperatorBot.\n\n**Stato:** {task_status}"
        label = "status: needs-review"

        if task_status == "FAILED":
            pr_title = f"fix: Tentativo fallito di eseguire task ({branch_name})"
            pr_body += f"\n\n**Log dell'Errore:**\n```\n{error_log}\n```"
            label = "status: failed"

        command = [
            'gh', 'pr', 'create',
            '--base', 'main',
            '--head', branch_name,
            '--title', pr_title,
            '--body', pr_body,
            '--label', label
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True, env=env)
        logging.info(f"✅ Pull Request creata: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        if "A pull request for" in e.stderr and "already exists" in e.stderr:
            logging.warning("Una Pull Request per questo branch esiste già.")
            return True
        logging.error(f"❌ Creazione Pull Request fallita: {e.stderr}")
        return False

def main():
    setup_logging()
    branch_name = os.getenv("BRANCH_NAME")
    task_description = os.getenv("TASK_DESCRIPTION")
    task_line_index = int(os.getenv("TASK_LINE_INDEX"))
    repo_path = os.getenv('GITHUB_WORKSPACE', os.getcwd())

    if not all([branch_name, task_description, task_line_index is not None]):
        logging.critical("Errore: mancano variabili d'ambiente necessarie."); exit(1)
        
    logging.info(f"--- OperatorBot: Avviato per il task: '{task_description}' ---")
    
    try:
        repo = Repo(repo_path)
        repo.git.config("user.name", "VARCAVIA Office Bot")
        repo.git.config("user.email", "bot@varcavia.com")
        
        if branch_name not in repo.heads:
            repo.create_head(branch_name).checkout()
        else:
            repo.heads[branch_name].checkout()
        logging.info(f"Spostato sul branch: {branch_name}")

        state_utils.update_task_status(task_line_index, "IN_PROGRESS")
        
        match = re.search(r'\[(.*?)\]', task_description)
        if not match: raise ValueError(f"Marcatore di tipo task non trovato in '{task_description}'.")
        
        task_type = match.group(1)
        action_description = task_description.replace(f'[{task_type}]', '').strip()
        
        if task_type == 'shell-command':
            logging.info(f"Eseguo comando shell: '{action_description}'")
            # Crea le directory parent se necessario, rendendo il comando più robusto
            if 'touch' in action_description:
                dir_path = os.path.dirname(action_description.split(' ')[-1])
                if dir_path:
                    os.makedirs(os.path.join(repo_path, dir_path), exist_ok=True)
            subprocess.run(action_description, shell=True, check=True, cwd=repo_path)
        else:
            file_path = task_type
            logging.info(f"Generazione contenuto per il file: {file_path}")
            model = get_gemini_model(EXECUTION_MODEL)
            generated_content = generate_response(model, f"Scrivi il codice/contenuto per questo task: '{action_description}'. Fornisci solo il codice puro, senza spiegazioni o markdown.")
            if generated_content is None: raise Exception("Generazione del contenuto AI fallita.")
            full_path = os.path.join(repo_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f: f.write(generated_content)
            logging.info(f"File '{file_path}' creato/aggiornato.")

        repo.git.add(A=True)
        if not repo.is_dirty(untracked_files=True):
            logging.warning("Nessuna modifica rilevata. Task considerato completato.");
        else:
            commit_message = f"feat: Esegue il task '{task_description[:40]}...'"
            repo.git.commit('-m', commit_message)
            logging.info(f"Commit creato: '{commit_message}'")
        
        remote_url = f"https://x-access-token:{os.getenv('GITHUB_TOKEN')}@github.com/{os.getenv('GITHUB_REPOSITORY')}.git"
        repo.git.push(remote_url, f'HEAD:{branch_name}', '--force')
        logging.info(f"Push del branch '{branch_name}' completato.")
        
        create_pull_request(branch_name, "DONE")
        state_utils.update_task_status(task_line_index, "DONE")

    except Exception as e:
        error_log = f"{type(e).__name__}: {e}"
        logging.critical(f"❌ Errore critico durante l'esecuzione del task: {error_log}", exc_info=True)
        # Tenta di creare una PR di fallimento
        create_pull_request(branch_name, "FAILED", error_log)
        state_utils.update_task_status(task_line_index, "FAILED")
        exit(1)

    logging.info(f"--- OperatorBot: Task completato. ---")

if __name__ == "__main__":
    main()