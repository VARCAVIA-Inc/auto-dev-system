import os
import logging
from git import Repo
from urllib.parse import urlparse, urlunparse

def push_changes_to_branch(repo_path, commit_message, branch_name):
    """
    Committa e pusha le modifiche a un branch specifico.
    """
    github_token = os.getenv("GITHUB_TOKEN")
    github_user = os.getenv("GITHUB_USER", "x-access-token") # Default per i token delle app

    if not github_token:
        logging.error("Errore: GITHUB_TOKEN non inizializzato.")
        return False

    logging.info(f"Tentativo di pushare al branch '{branch_name}' con messaggio: '{commit_message}'")
    try:
        repo = Repo(repo_path)
        repo.git.add(all=True)

        if not repo.index.diff("HEAD"):
            logging.warning("Nessuna modifica rilevata da committare.")
            return True

        repo.index.commit(commit_message)
        logging.info(f"Modifiche committate localmente: '{commit_message}'.")

        origin = repo.remote(name='origin')
        
        # Costruisce l'URL di autenticazione in modo sicuro
        parsed_url = urlparse(origin.url)
        netloc_part = parsed_url.netloc.split('@', 1)[-1] if '@' in parsed_url.netloc else parsed_url.netloc
        auth_url = urlunparse(parsed_url._replace(netloc=f"{github_user}:{github_token}@{netloc_part}"))
        
        repo.git.push(auth_url, branch_name)
        logging.info(f"✅ Modifiche pushat-e con successo al branch '{branch_name}'.")
        return True
    except Exception as e:
        logging.error(f"❌ Errore durante il push delle modifiche: {e}", exc_info=True)
        return False