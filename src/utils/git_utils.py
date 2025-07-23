import os
import logging
from git import Repo

def commit_and_push_changes(repo_path, commit_message, branch_name):
    """Committa e pusha le modifiche a un branch specifico."""
    github_token = os.getenv("GITHUB_TOKEN")
    repo_slug = os.getenv("GITHUB_REPOSITORY")

    if not github_token or not repo_slug:
        logging.error("Errore: GITHUB_TOKEN o GITHUB_REPOSITORY non inizializzati.")
        return False

    logging.info(f"Push delle modifiche al branch '{branch_name}'...")
    try:
        repo = Repo(repo_path)
        
        # Aggiunge tutti i file modificati e nuovi
        repo.git.add(A=True)

        if not repo.is_dirty(untracked_files=True):
            logging.warning("Nessuna modifica da committare.")
            return True

        repo.index.commit(commit_message)
        logging.info(f"Commit creato: '{commit_message}'.")

        remote_url = f"https://x-access-token:{github_token}@github.com/{repo_slug}.git"
        
        repo.git.push(remote_url, branch_name)
        logging.info(f"✅ Modifiche inviate con successo al branch '{branch_name}'.")
        return True
    except Exception as e:
        logging.error(f"❌ Errore durante il push delle modifiche: {e}", exc_info=True)
        return False