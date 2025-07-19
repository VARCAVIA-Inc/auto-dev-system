import os
import logging
import re
import subprocess
from git import Repo
from src.utils.logging_utils import setup_logging
from src.utils.ai_utils import get_gemini_model, generate_response, EXECUTION_MODEL

def create_pull_request(branch_name):
    """Crea una Pull Request usando la CLI di GitHub."""
    try:
        logging.info(f"Creazione della Pull Request per il branch '{branch_name}'...")
        env = os.environ.copy()
        env['GH_TOKEN'] = os.getenv("GITHUB_TOKEN")
        
        command = f"gh pr create --base main --head \"{branch_name}\" --fill"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True, env=env)
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
    commit_message = os.getenv("COMMIT_MESSAGE")
    repo_path = os.getenv('GITHUB_WORKSPACE', os.getcwd())

    if not all([branch_name, task_description, commit_message]):
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
        
        match = re.search(r'\[(.*?)\]', task_description)
        if not match: raise ValueError("Marcatore di tipo task non trovato.")
        
        task_type = match.group(1)
        action_description = task_description.replace(f'[{task_type}]', '').strip()
        
        if task_type == 'shell-command':
            logging.info(f"Eseguo comando shell: '{action_description}'")
            subprocess.run(action_description, shell=True, check=True, cwd=repo_path)
        else:
            file_path = task_type
            logging.info(f"Generazione contenuto per il file: {file_path}")
            
            model = get_gemini_model(EXECUTION_MODEL)
            generated_content = generate_response(model, f"Scrivi il codice/contenuto per questo task: '{action_description}'. Fornisci solo il codice puro, senza spiegazioni o markdown.")
            if not generated_content: raise Exception("Generazione del contenuto AI fallita.")
            
            full_path = os.path.join(repo_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f: f.write(generated_content)
            logging.info(f"File '{file_path}' creato/aggiornato.")
        
        repo.git.add(all=True)
        if not repo.index.diff("HEAD"):
            logging.warning("Nessuna modifica rilevata. Task completato senza PR."); return
            
        repo.index.commit('-m', commit_message)
        logging.info(f"Commit creato: '{commit_message}'")
        
        remote_url = f"https://x-access-token:{os.getenv('GITHUB_TOKEN')}@github.com/{os.getenv('GITHUB_REPOSITORY')}.git"
        repo.remote(name='origin').push(refspec=f'{branch_name}:{branch_name}', url=remote_url)
        logging.info(f"Push del branch '{branch_name}' completato.")
        
        create_pull_request(branch_name)

    except Exception as e:
        logging.critical(f"❌ Errore critico durante l'esecuzione del task: {e}", exc_info=True); exit(1)

    logging.info(f"--- OperatorBot: Task completato. ---")

if __name__ == "__main__":
    main()