import os
import logging
import re
import subprocess
from git import Repo
from src.utils.logging_utils import setup_logging
from src.utils.ai_utils import get_gemini_model, generate_response, EXECUTION_MODEL

def generate_code_with_ai(task_description):
    """Genera il codice o il contenuto per un task specifico."""
    prompt = (
        f"Sei un OperatorBot, un bot sviluppatore esperto. Il tuo unico obiettivo è scrivere il codice o il contenuto necessario per completare il seguente task. "
        f"NON aggiungere spiegazioni, commenti o testo introduttivo. Fornisci solo il codice/contenuto richiesto, pronto per essere scritto direttamente in un file.\n\n"
        f"Task da eseguire: '{task_description}'"
    )
    try:
        model = get_gemini_model(EXECUTION_MODEL)
        generated_content = generate_response(model, prompt)
        if generated_content:
            # Pulisce il codice da eventuali blocchi di markdown
            if generated_content.strip().startswith("```") and generated_content.strip().endswith("```"):
                cleaned_content = '\n'.join(generated_content.strip().split('\n')[1:-1])
                return cleaned_content
            return generated_content.strip()
        return None
    except Exception as e:
        logging.critical(f"Impossibile generare codice: {e}")
        return None

def create_pull_request(branch_name, pr_title, pr_body):
    """Crea una Pull Request usando la CLI di GitHub."""
    try:
        logging.info(f"Creazione della Pull Request per il branch '{branch_name}'...")
        env = os.environ.copy()
        env['GH_TOKEN'] = os.getenv("GITHUB_TOKEN")
        
        # Comando per creare la PR. L'opzione --fill usa il primo commit per titolo e corpo.
        gh_command = f"gh pr create --base main --head \"{branch_name}\" --fill"
        
        result = subprocess.run(gh_command, shell=True, capture_output=True, text=True, check=True, env=env)
        logging.info(f"✅ Pull Request creata con successo: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Creazione Pull Request fallita. Errore: {e.stderr}")
        # Controlla se la PR esiste già
        if "A pull request for" in e.stderr and "already exists" in e.stderr:
            logging.warning("Una Pull Request per questo branch esiste già.")
            return True
        return False

def main():
    setup_logging()
    branch_name = os.getenv("BRANCH_NAME")
    task_description = os.getenv("TASK_DESCRIPTION")
    commit_message = os.getenv("COMMIT_MESSAGE")
    repo_path = os.getenv('GITHUB_WORKSPACE', os.getcwd())

    if not all([branch_name, task_description, commit_message]):
        logging.critical("Errore: mancano le variabili d'ambiente necessarie (BRANCH_NAME, TASK_DESCRIPTION, COMMIT_MESSAGE)."); exit(1)
        
    logging.info(f"--- OperatorBot: Avviato sul branch '{branch_name}' per il task: '{task_description}' ---")
    
    try:
        repo = Repo(repo_path)
        repo.git.config("user.name", "VARCAVIA Office Bot")
        repo.git.config("user.email", "bot@varcavia.com")
        
        # Creazione e checkout del nuovo branch
        if branch_name not in repo.heads:
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()
            logging.info(f"Creato e spostato sul nuovo branch: {branch_name}")
        else:
            repo.heads[branch_name].checkout()
            logging.info(f"Spostato sul branch esistente: {branch_name}")
        
        match = re.search(r'\[(.*?)\]', task_description)
        if not match: raise ValueError(f"Marcatore di tipo task non trovato in '{task_description}'.")
        
        task_type = match.group(1)
        action_description = task_description.replace(f'[{task_type}]', '').strip()
        
        if task_type == 'shell-command':
            logging.info(f"Eseguo comando shell: '{action_description}'")
            subprocess.run(action_description, shell=True, check=True, cwd=repo_path)
        else:
            file_path = task_type
            logging.info(f"File target identificato: {file_path}")
            
            generated_content = generate_code_with_ai(task_description)
            if generated_content is None: raise Exception("La generazione del contenuto AI è fallita.")
            
            full_path = os.path.join(repo_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w') as f: f.write(generated_content)
            logging.info(f"File '{file_path}' creato/aggiornato.")
        
        # Commit e Push
        repo.git.add(all=True)
        if not repo.index.diff("HEAD"):
            logging.warning("Nessuna modifica rilevata. Task completato senza creare una PR."); return
            
        repo.git.commit('-m', commit_message)
        logging.info(f"Commit creato con messaggio: '{commit_message}'")
        
        # Push
        origin = repo.remote(name='origin')
        origin.push(refspec=f'{branch_name}:{branch_name}')
        logging.info(f"Push del branch '{branch_name}' completato.")
        
        # Creazione Pull Request
        create_pull_request(branch_name, commit_message, f"PR automatica per: {task_description}")

    except Exception as e:
        logging.critical(f"❌ Un errore è occorso durante l'esecuzione del task: {e}", exc_info=True); exit(1)

    logging.info(f"--- OperatorBot: Task '{task_description}' completato con successo. ---")

if __name__ == "__main__":
    main()