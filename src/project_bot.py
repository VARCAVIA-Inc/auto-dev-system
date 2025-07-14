import os
import openai
from src.utils.email_sender import send_email
import yaml
from git import Repo, exc # Ri-includi per la gestione Git locale nel push trigger
# Rimuovi PyGithubClient, non sarà in questo file
# from github import Github as PyGithubClient
from urllib.parse import urlparse, urlunparse # Può rimanere, non danneggia


# Variabili Globali per le credenziali (verranno impostate da init_project_bot_env)
_openai_api_key = None
_receiver_email = None
_sender_email = None
_github_token = None
# _github_api_client = None # Non più necessario per questo file

def init_project_bot_env(openai_api_key, receiver_email, sender_email, github_token):
    # ... (Questa funzione rimane uguale) ...
    global _openai_api_key, _receiver_email, _sender_email, _github_token
    _openai_api_key = openai_api_key
    _receiver_email = receiver_email
    _sender_email = sender_email
    _github_token = github_token
    openai.api_key = openai_api_key
    print("Project-Bot Environment Inizializzato.")

# Rimuovi get_repo_obj() e commit_and_push_on_new_branch() da qui.
# Sono ora nel nuovo workflow separato, non devono essere qui.

def get_repo_root():
    """Restituisce il percorso della radice del repository."""
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

# NUOVA funzione per pushare i file di trigger al branch main
def push_trigger_files_to_main(repo_path, commit_message):
    """
    Esegue un git add . e pusha al branch main i file modificati localmente.
    Questo serve ad attivare il workflow secondario.
    """
    global _github_token, _receiver_email, _sender_email

    if not _github_token:
        print("Errore: GITHUB_TOKEN non inizializzato per il push dei trigger. Impossibile pushare.")
        return False

    print(f"Tentativo di pushare i file di trigger al branch main con messaggio: '{commit_message}'")
    try:
        repo = Repo(repo_path)
        
        # Aggiungi tutte le modifiche (incluso .autodev-trigger e business_plan.yaml)
        repo.git.add(all=True)
        print("Tutte le modifiche aggiunte all'indice Git per il push del trigger.")

        if not repo.index.diff("HEAD"):
            print("Nessuna modifica stageata da committare per il push del trigger. Saltando.")
            return True

        repo.index.commit(commit_message)
        print(f"Modifiche committate localmente per il push del trigger: '{commit_message}'.")

        # Configura l'URL remoto con il token per il push
        origin = repo.remote(name='origin')
        original_url = origin.url
        parsed_url = urlparse(original_url)
        
        netloc_part = parsed_url.netloc.split('@', 1)[-1] if '@' in parsed_url.netloc else parsed_url.netloc
        auth_url = urlunparse(parsed_url._replace(netloc=f"oauth2:{_github_token}@{netloc_part}"))
        
        print(f"DEBUG: Impostazione URL remoto per push trigger: {auth_url.replace(_github_token, '*****')}")
        repo.git.remote('set-url', 'origin', auth_url)
        
        # Esegui il push sul branch main
        print("DEBUG: Eseguendo push sul branch main.")
        origin.push("main") # Push del branch locale 'main' al branch remoto 'main'
        
        # Ripristina l'URL originale
        repo.git.remote('set-url', 'origin', original_url)
        
        print("File di trigger e BP pushati con successo al branch 'main'.")
        return True
    except exc.GitCommandError as e:
        print(f"Errore Git durante il push dei file di trigger: {e}")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Errore Project-Bot: Push Trigger Fallito",
            body=f"Il Project-Bot non è riuscito a pushare i file di trigger al branch 'main'.\nErrore: {e}\nMessaggio: {commit_message}",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return False
    except Exception as e:
        print(f"Errore generico durante il push dei file di trigger: {e}")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Errore Project-Bot: Push Trigger Fallito (Generico)",
            body=f"Il Project-Bot ha riscontrato un errore generico durante il push dei file di trigger.\nErrore: {e}\nMessaggio: {commit_message}",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return False


# Funzioni principali del Project-Bot
def generate_response_with_ai(prompt, model="gpt-4o-mini"):
    # ... (questa funzione rimane uguale) ...
    pass

def create_file_task(task_details):
    # ... (questa funzione rimane uguale) ...
    pass

def update_business_plan_status(task_index, phase_index, new_status="completed"):
    # ... (questa funzione rimane uguale) ...
    pass

def run_project_bot(task_details, task_index, phase_index):
    # ... (inizio della funzione run_project_bot) ...
    global _receiver_email, _sender_email 
    task_description = task_details.get('description', 'N/A')
    task_type = task_details.get('type')
    
    print(f"Inizio esecuzione run_project_bot per task: '{task_description}' (Tipo: {task_type}).")
    print(f"Task details completi: {task_details}")
    
    task_completed = False
    commit_message = f"feat: {task_description[:70]}..." # Per il commit del trigger

    # 1. Esegui l'azione del task
    if task_type == 'create_file':
        print("Rilevato task_type 'create_file'. Chiamata create_file_task.")
        task_completed = create_file_task(task_details)
        if task_completed:
            print("create_file_task completato con successo.")
        else:
            print("create_file_task ha restituito False (fallimento).")
        commit_message = f"feat: Create file {task_details.get('path', 'unknown')}"
    elif task_type == 'info' or task_type == 'action' or task_type == 'generate_code':
        print(f"Rilevato task_type '{task_type}'. Processando via AI prompt.")
        ai_prompt = f"Genera un messaggio per il completamento del seguente task: '{task_description}'."
        ai_response = generate_response_with_ai(ai_prompt)
        if ai_response:
            print(f"Risposta AI per il task '{task_description}': {ai_response}")
            task_completed = True
        else:
            print("Il Project-Bot non è riuscito a generare una risposta AI per il task info/action.")
            task_completed = False
        commit_message = f"chore: Processed info/action task: {task_description[:50]}"
    else:
        print(f"Tipo di task sconosciuto: {task_type}. Nessuna azione specifica.")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Sconosciuto: {task_description[:50]}...",
            body=f"Il Project-Bot ha incontrato un task con tipo sconosciuto: '{task_type}' per la descrizione: '{task_description}'.",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        task_completed = False

    # 2. Aggiorna lo stato del Business Plan (localmente)
    bp_update_successful = update_business_plan_status(task_index, phase_index, "completed" if task_completed else "failed")
    if not bp_update_successful:
        print("Errore: Fallimento nella scrittura locale dello stato del Business Plan. Non verrà creato alcun file di trigger.")
        task_completed = False

    # 3. Se il task è completato e BP aggiornato, crea il file di trigger e pusha al main.
    # Questo push attiverà il workflow git_pr_workflow.yml
    if task_completed and bp_update_successful:
        print("Task completato e BP aggiornato localmente. Creazione file di trigger per il workflow Git/PR.")
        trigger_file_path = os.path.join(get_repo_root(), ".autodev-trigger")
        try:
            with open(trigger_file_path, 'w') as f:
                f.write(f"task_status: {'completed'}\n")
                f.write(f"commit_message: {commit_message}\n")
                f.write(f"timestamp: {os.getenv('GITHUB_RUN_ID')}\n")
            print(f"File di trigger '{trigger_file_path}' creato con successo.")
            
            # Esegui il push dei file di trigger al branch main
            # Questo push conterrà .autodev-trigger e le modifiche al business_plan.yaml e welcome.txt
            if push_trigger_files_to_main(get_repo_root(), f"chore: AutoDevSystem trigger for '{commit_message}'"):
                send_email(
                    subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Completato Localmente: {task_description[:50]}...",
                    body=f"Il Project-Bot ha completato il task:\n'{task_description}'\n\nIl Business Plan e il file di trigger sono stati pushati al branch main. Attendi la Pull Request dal workflow secondario.",
                    to_email=_receiver_email,
                    sender_email=_sender_email
                )
            else:
                print("Avviso: Task completato localmente, ma push dei file di trigger al main fallito.")
                send_email(
                    subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Completato (Push Trigger Fallito): {task_description[:50]}...",
                    body=f"Il Project-Bot ha completato il task:\n'{task_description}'\n\nMA non è riuscito a pushare i file di trigger al branch main. Il workflow secondario non si attiverà. Controllare i log.",
                    to_email=_receiver_email,
                    sender_email=_sender_email
                )

        except Exception as e:
            print(f"Errore nella creazione del file di trigger: {e}")
            send_email(
                subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Errore Creazione Trigger: {task_description[:50]}...",
                body=f"Il Project-Bot ha completato il task localmente ma non è riuscito a creare il file di trigger per il push/PR.\nErrore: {e}",
                to_email=_receiver_email,
                sender_email=_sender_email
            )
    else:
        print("Task fallito o BP non aggiornato localmente. Nessun file di trigger creato.")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Fallito: {task_description[:50]}...",
            body=f"Il Project-Bot non è riuscito a completare il task:\n'{task_description}'.\n\nControlla i log di GitHub Actions per i dettagli.",
            to_email=_receiver_email,
            sender_email=_sender_email
        )

    print("Fine esecuzione run_project_bot.")

if __name__ == "__main__":
    pass