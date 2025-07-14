import os
import openai
from src.utils.email_sender import send_email # Nota: send_email leggerà da os.getenv
import yaml
from git import Repo, exc
from github import Github as PyGithubClient
from urllib.parse import urlparse, urlunparse

# Variabili Globali per le credenziali (verranno impostate da init_project_bot_env)
# Rimuoviamo l'uso di _openai_api_key nelle funzioni chiamate per iniettarla direttamente
_receiver_email = None
_sender_email = None
_github_token = None
_github_api_client = None

def init_project_bot_env(openai_api_key, receiver_email, sender_email, github_token):
    """
    Inizializza le variabili d'ambiente per il Project-Bot.
    Questa funzione deve essere chiamata dal Manager-Bot prima di run_project_bot.
    """
    global _receiver_email, _sender_email, _github_token, _github_api_client
    _receiver_email = receiver_email
    _sender_email = sender_email
    _github_token = github_token
    # Non impostiamo openai.api_key qui; la passeremo direttamente alla funzione generate_response_with_ai
    # Questo assicura che il modulo openai non sia inizializzato con un valore potenzialmente nullo/vuoto in anticipo.

    # Inizializza il client PyGithub per API calls (creare branch/PR remoti)
    try:
        _github_api_client = PyGithubClient(_github_token)
        print("PyGithub client inizializzato.")
    except Exception as e:
        print(f"Errore nell'inizializzazione del client PyGithub: {e}")
        # Usiamo os.getenv per l'email qui, dato che _receiver_email potrebbe non essere ancora impostato
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore Project-Bot: Inizializzazione PyGithub",
            body=f"Il Project-Bot non è riuscito a inizializzare il client PyGithub.\nErrore: {e}",
            to_email=os.getenv("RECEIVER_EMAIL"),
            sender_email=os.getenv("SENDER_EMAIL")
        )
        _github_api_client = None
    
    print("Project-Bot Environment Inizializzato.")

# Funzioni ausiliarie per la gestione del repository Git (non cambiano)
def get_repo_root():
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

def get_repo_obj():
    global _github_api_client
    if not _github_api_client:
        print("Errore: Client PyGithub non inizializzato.")
        return None
    try:
        repo_name = os.getenv("GITHUB_REPOSITORY") 
        if not repo_name:
            print("Errore: GITHUB_REPOSITORY non impostato.")
            return None
        return _github_api_client.get_repo(repo_name)
    except Exception as e:
        print(f"Errore nel recupero dell'oggetto repository di PyGithub: {e}")
        return None

def commit_and_push_on_new_branch(repo_path, commit_message, base_branch="main", new_branch_prefix="autodev-task-"):
    global _github_token, _github_api_client, _receiver_email, _sender_email
    
    if not _github_token or not _github_api_client:
        print("Errore: Credenziali GitHub non inizializzate per commit/push/PR. Impossibile procedere.")
        return False

    print(f"Tentativo di commit e push: '{commit_message}'")

    try:
        repo = Repo(repo_path)
        
        repo.git.add(all=True)
        print("Tutte le modifiche aggiunte all'indice Git.")
        
        if not repo.index.diff("HEAD"):
            print("Nessuna modifica stageata da committare. Saltando push e PR.")
            return True

        timestamp = os.getenv('GITHUB_RUN_ID', 'manual')
        new_branch_name = f"{new_branch_prefix}{timestamp}"
        
        new_local_branch = repo.create_head(new_branch_name)
        new_local_branch.checkout()
        
        print(f"Creato e passato al nuovo branch locale: {new_branch_name}")

        repo.index.commit(commit_message)
        print(f"Modifiche committate sul branch {new_branch_name}.")

        origin = repo.remote(name='origin')
        print(f"Pushing al branch: {new_branch_name} usando l'autenticazione implicita di GitHub Actions.")
        origin.push(f"{new_branch_name}:{new_branch_name}")
        print(f"Modifiche pushati al branch remoto '{new_branch_name}' con successo.")

        repo_obj = get_repo_obj()
        if not repo_obj:
            print("Errore: Impossibile recuperare l'oggetto repository di PyGithub per creare la PR.")
            send_email(
                subject=f"[AUTO-DEV-SYSTEM] Avviso: PR non creata (Project-Bot)",
                body=f"Il Project-Bot ha completato il task e pushato le modifiche al branch '{new_branch_name}', ma non è riuscito a creare la Pull Request a causa di un problema con l'accesso all'API del repository.",
                to_email=_receiver_email,
                sender_email=_sender_email
            )
            return False
        
        pr_title = f"[AutoDevTask] {commit_message}"
        pr_body = (
            f"Questo branch è stato generato automaticamente dall'AutoDevSystem in risposta a un task del Business Plan.\n\n"
            f"**Task:** {commit_message}\n"
            f"**Branch:** `{new_branch_name}`\n\n"
            "Si prega di revisionare e unire."
        )
        pull_request = repo_obj.create_pull(title=pr_title, body=pr_body, head=new_branch_name, base=base_branch)
        print(f"Pull Request creata: {pull_request.html_url}")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Nuova Pull Request: {pr_title}",
            body=f"Il Project-Bot ha completato un task e aperto una nuova Pull Request.\n\nTitolo: {pr_title}\nLink PR: {pull_request.html_url}\n\nSi prega di revisionare e unire.",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return True

    except exc.GitCommandError as e:
        print(f"Errore Git nel commit_and_push_on_new_branch: {e}")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Errore Git nel Project-Bot (Branch/PR)",
            body=f"Il Project-Bot ha riscontrato un errore Git durante la creazione del branch, commit o push.\nErrore: {e}\nMessaggio: {commit_message}",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return False
    except Exception as e:
        print(f"Errore generico in commit_and_push_on_new_branch: {e}")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Errore generico nel Project-Bot (Branch/PR)",
            body=f"Il Project-Bot ha riscontrato un errore generico durante la gestione del branch/PR.\nErrore: {e}\nMessaggio: {commit_message}",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return False