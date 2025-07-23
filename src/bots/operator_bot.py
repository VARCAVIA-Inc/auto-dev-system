import os
import logging
import re
import subprocess
from git import Repo
from src.utils.logging_utils import setup_logging
from src.utils.ai_utils import get_gemini_model, generate_response, EXECUTION_MODEL

def create_pull_request(branch_name, commit_message):
    """Crea una Pull Request usando il commit message come titolo e corpo."""
    try:
        logging.info(f"Creazione della Pull Request per il branch '{branch_name}'...")
        env = os.environ.copy()
        env['GH_TOKEN'] = os.getenv("BOT_GITHUB_TOKEN") # Usa il token del bot per l'autenticazione
        
        # Usa --title e --body per un controllo esplicito
        command = [
            'gh', 'pr', 'create',
            '--base', 'main',
            '--head', branch_name,
            '--title', commit_message,
            '--body', f"Questa PR è stata generata automaticamente per completare il task:\n`{os.getenv('TASK_DESCRIPTION')}`"
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True, env=env)
        logging.info(f"✅ Pull Request creata con successo: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        if "A pull request for" in e.stderr and "already exists" in e.stderr:
            logging.warning(f"Una Pull Request per il branch '{branch_name}' esiste già. Nessuna nuova azione richiesta.")
            return True
        logging.error(f"❌ Errore durante la creazione della Pull Request: {e.stderr}")
        return False

def main():
    setup_logging()
    branch_name = os.getenv("BRANCH_NAME")
    task_description = os.getenv("TASK_DESCRIPTION")
    commit_message = os.getenv("COMMIT_MESSAGE")
    repo_path = os.getenv('GITHUB_WORKSPACE', os.getcwd())

    if not all([branch_name, task_description, commit_message]):
        logging.critical("Errore critico: mancano le variabili d'ambiente necessarie (BRANCH_NAME, TASK_DESCRIPTION, COMMIT_MESSAGE). Interruzione.")
        exit(1)
        
    logging.info(f"--- OperatorBot: Avviato per il task: '{task_description}' ---")
    
    try:
        repo = Repo(repo_path)
        repo.git.config("user.name", "VARCAVIA Office Bot")
        repo.git.config("user.email", "bot@varcavia.com")
        
        # Crea e passa al nuovo branch
        if branch_name in repo.heads:
            repo.heads[branch_name].checkout()
        else:
            repo.create_head(branch_name).checkout()
        logging.info(f"Spostato sul branch: '{branch_name}'")
        
        # Estrae il target e la descrizione dell'azione
        match = re.search(r'\[(shell-command|.*?)\]\s*(.*)', task_description)
        if not match or len(match.groups()) < 2:
            raise ValueError(f"Formato del task non valido. Impossibile estrarre [target] e descrizione da: '{task_description}'")
        
        target = match.group(1)
        action_description = match.group(2).strip()
        
        if target == 'shell-command':
            logging.info(f"Esecuzione del comando shell: '{action_description}'")
            # Il comando è la descrizione stessa
            subprocess.run(action_description, shell=True, check=True, cwd=repo_path)
        else:
            file_path = target
            logging.info(f"Generazione contenuto per il file: '{file_path}' basato su: '{action_description}'")
            model = get_gemini_model(EXECUTION_MODEL)
            prompt = f"Sei un ingegnere software esperto. Il tuo unico compito è generare il contenuto completo di un file di codice basandoti su una specifica richiesta. Fornisci solo e unicamente il codice sorgente pulito, senza alcuna spiegazione, commento introduttivo o ```markdown fences```. Il codice deve essere pronto per essere scritto direttamente su un file.\n\nRichiesta: '{action_description}'\nContenuto del file '{file_path}':"
            
            generated_content = generate_response(model, prompt)
            if generated_content is None:
                raise Exception("La generazione del contenuto da parte dell'IA non ha prodotto risultati.")
                
            full_path = os.path.join(repo_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(generated_content)
            logging.info(f"File '{file_path}' creato/aggiornato con successo.")
        
        # L'OPERATORE NON ESEGUE PIÙ I TEST. LA VALIDAZIONE È FATTA NELLA PR.
        
        repo.git.add(all=True)
        if not repo.is_dirty(untracked_files=True):
            logging.warning("Nessuna modifica al codice rilevata. Il task potrebbe essere già stato completato o non ha prodotto codice. Concludo il task senza creare una PR.")
            return
            
        repo.git.commit('-m', commit_message)
        logging.info(f"Commit creato con messaggio: '{commit_message}'")
        
        # Esegue il push sul branch remoto
        remote_url = f"https://x-access-token:{os.getenv('BOT_GITHUB_TOKEN')}@github.com/{os.getenv('GITHUB_REPOSITORY')}.git"
        repo.git.push(remote_url, f'HEAD:{branch_name}', '--force')
        logging.info(f"Push del branch '{branch_name}' al remote completato.")
        
        # Crea la Pull Request
        if not create_pull_request(branch_name, commit_message):
            raise Exception("Fallimento critico nella creazione della Pull Request.")

    except Exception as e:
        logging.critical(f"❌ Errore critico durante l'esecuzione del task: {e}", exc_info=True)
        exit(1)

    logging.info(f"--- OperatorBot: Task completato e Pull Request creata/aggiornata. In attesa della validazione. ---")

if __name__ == "__main__":
    main()