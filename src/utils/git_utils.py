import os
from git import Repo
from urllib.parse import urlparse, urlunparse

def push_changes_to_main(repo_path, commit_message):
    github_token = os.getenv("GITHUB_TOKEN")
    github_user = os.getenv("GITHUB_USER")

    if not github_token or not github_user:
        print("Errore: GITHUB_TOKEN o GITHUB_USER non inizializzati.")
        return False

    print(f"Tentativo di pushare le modifiche al branch main con messaggio: '{commit_message}'")
    try:
        repo = Repo(repo_path)
        repo.git.add(all=True)

        if not repo.index.diff("HEAD"):
            print("Nessuna modifica da committare.")
            return True

        repo.index.commit(commit_message)
        print(f"Modifiche committate localmente: '{commit_message}'.")

        origin = repo.remote(name='origin')
        parsed_url = urlparse(origin.url)
        netloc_part = parsed_url.netloc.split('@', 1)[-1] if '@' in parsed_url.netloc else parsed_url.netloc
        auth_url = urlunparse(parsed_url._replace(netloc=f"{github_user}:{github_token}@{netloc_part}"))
        
        repo.git.push(auth_url, "main")
        print("Modifiche pushat-e con successo al branch 'main'.")
        return True
    except Exception as e:
        print(f"Errore durante il push delle modifiche: {e}")
        return False