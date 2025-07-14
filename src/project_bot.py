import os
import openai
from src.utils.email_sender import send_email
import yaml
from git import Repo, exc
from github import Github as PyGithubClient
from urllib.parse import urlparse, urlunparse

# Variabili Globali per le credenziali (verranno impostate da init_project_bot_env)
_openai_api_key = None
_receiver_email = None
_sender_email = None
_github_token = None
_github_api_client = None

def init_project_bot_env(openai_api_key, receiver_email, sender_email, github_token):
    """
    Inizializza le variabili d'ambiente per il Project-Bot.
    Questa funzione deve essere chiamata dal Manager-Bot prima di run_project_bot.
    """
    global _openai_api_key, _receiver_email, _sender_email, _github_token, _github_api_client
    _openai_api_key = openai_api_key
    _receiver_email = receiver_email
    _sender_email = sender_email
    _github_token = github_token
    openai.api_key = openai_api_key # Imposta la chiave API di OpenAI per il client

    # Inizializza il client PyGithub per API calls (creare branch/PR remoti)
    try:
        _github_api_client = PyGithubClient(_github_token)
        print("PyGithub client inizializzato.")
    except Exception as e:
        print(f"Errore nell'inizializzazione del client PyGithub: {e}")
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore Project-Bot: Inizializzazione PyGithub",
            body=f"Il Project-Bot non è riuscito a inizializzare il client PyGithub.\nErrore: {e}",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        _github_api_client = None
    
    print("Project-Bot Environment Inizializzato.")

# Funzioni ausiliarie per la gestione del repository Git
def get_repo_root():
    """Restituisce il percorso della radice del repository."""
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

def get_repo_obj():
    """Restituisce l'oggetto repository di PyGithub."""
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
    """
    Crea un nuovo branch, committa le modifiche e pusha sul nuovo branch, poi apre una PR.
    """
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

# Funzioni principali del Project-Bot
def generate_response_with_ai(prompt, model="gpt-4o-mini"):
    """
    Genera una risposta usando l'API di OpenAI.
    """
    global _openai_api_key 
    if not _openai_api_key:
        print("Errore: OPENAI_API_KEY non configurata per la chiamata AI. Impossibile generare contenuto.")
        return None
    
    print(f"DEBUG: Tentativo di chiamata OpenAI API. Prompt: {prompt[:100]}...") # <--- NUOVO DEBUG
    
    try:
        completion = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Sei un assistente AI utile e specializzato nella generazione di codice e contenuti tecnici."},
                {"role": "user", "content": prompt}
            ]
        )
        print("Risposta OpenAI ricevuta.")
        return completion.choices[0].message.content
    except openai.AuthenticationError as e: # <--- CATTURA ERRORE DI AUTENTICAZIONE SPECIFICO
        print(f"Errore di autenticazione OpenAI: {e}. Controlla la OPENAI_API_KEY.")
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore di Autenticazione OpenAI",
            body=f"Il Project-Bot ha riscontrato un errore di autenticazione con l'API di OpenAI.\nErrore: {e}\nAssicurati che OPENAI_API_KEY sia corretta e valida.",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return None
    except openai.APICallError as e: # <--- CATTURA ERRORI GENERALI API CALL
        print(f"Errore durante la chiamata API OpenAI: {e}. Code: {e.code}, Type: {e.type}")
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore API OpenAI",
            body=f"Il Project-Bot ha riscontrato un errore durante la chiamata API di OpenAI.\nErrore: {e}\nCode: {e.code}, Type: {e.type}",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return None
    except Exception as e:
        print(f"Errore generico durante la chiamata OpenAI: {e}. Tipo: {type(e)}") # <--- DEBUG TYPE
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Errore Project-Bot (OpenAI Generico)",
            body=f"Il Project-Bot ha riscontrato un errore generico durante la chiamata OpenAI.\nErrore: {e}\nTipo: {type(e)}",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return None

def create_file_task(task_details):
    """
    Gestisce il task di creazione di un file.
    """
    print("Inizio funzione create_file_task.")
    file_path = task_details.get('path')
    prompt_for_content = task_details.get('prompt_for_content')

    print(f"Dettagli task creazione file: path='{file_path}', prompt_for_content='{prompt_for_content[:50]}...'")

    if not file_path:
        print("Errore: 'path' non specificato per il task 'create_file'. Restituisco False.")
        return False

    print(f"Tentativo di creazione file: {file_path}")
    content = ""
    if prompt_for_content:
        print(f"Generando contenuto AI per il file: {file_path}...")
        try: # <--- AGGIUNTO TRY/EXCEPT QUI
            ai_generated_content = generate_response_with_ai(prompt_for_content)
        except Exception as e:
            print(f"Errore inaspettato durante la chiamata generate_response_with_ai: {e}")
            ai_generated_content = None # Assicurati che sia None in caso di eccezione inattesa
        
        if ai_generated_content:
            content = ai_generated_content
        else:
            print("Impossibile generare contenuto AI. Il file non verrà creato. Restituisco False.")
            return False

    try:
        dir_name = os.path.dirname(file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        
        full_path = os.path.join(get_repo_root(), file_path)
        print(f"Scrivendo il file completo in: {full_path}")
        with open(full_path, 'w') as f:
            f.write(content)
        print(f"File '{full_path}' creato/aggiornato con successo.")
        return True
    except Exception as e:
        print(f"Errore durante la creazione del file '{file_path}': {e}. Restituisco False.")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Errore Project-Bot: Creazione file fallita",
            body=f"Il Project-Bot non è riuscito a creare il file '{file_path}'.\nErrore: {e}",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return False

def update_business_plan_status(task_index, phase_index, new_status="completed"):
    # ... (questa funzione rimane uguale) ...
    pass

def run_project_bot(task_details, task_index, phase_index):
    # ... (il resto di questa funzione rimane uguale) ...
    global _receiver_email, _sender_email 
    task_description = task_details.get('description', 'N/A')
    task_type = task_details.get('type')
    
    print(f"Inizio esecuzione run_project_bot per task: '{task_description}' (Tipo: {task_type}).")
    print(f"Task details completi: {task_details}")
    
    task_completed = False
    commit_message = f"feat: {task_description[:70]}..."

    # 1. Esegui l'azione del task
    if task_type == 'create_file':
        print("Rilevato task_type 'create_file'. Chiamata create_file_task.")
        task_completed = create_file_task(task_details) # <-- La logica di successo/fallimento è qui
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
        print("Errore: Fallimento nella scrittura locale dello stato del Business Plan.")
        task_completed = False # Considera il task fallito se non si può aggiornare il BP

    # 3. Committa e pusha le modifiche sul nuovo branch e crea PR (se ci sono modifiche)
    if task_completed and bp_update_successful:
        print("Tentativo di commit e push su nuovo branch e creazione PR.")
        push_and_pr_successful = commit_and_push_on_new_branch(get_repo_root(), commit_message)
        
        # 4. Notifica finale via email
        if push_and_pr_successful:
            send_email(
                subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Completato e PR Creata: {task_description[:50]}...",
                body=f"Il Project-Bot ha completato con successo il task:\n'{task_description}'\n\nÈ stata creata una Pull Request per unire le modifiche. Controlla il tuo repository GitHub.",
                to_email=_receiver_email,
                sender_email=_sender_email
            )
        else:
            print("Avviso: Task completato localmente, ma push o PR falliti.")
            send_email(
                subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Completato (Richiede Intervento Manuale): {task_description[:50]}...",
                body=f"Il Project-Bot ha completato il task:\n'{task_description}'\n\n**ATTENZIONE:** Il push delle modifiche o la creazione della Pull Request sono falliti. Controllare i log di GitHub Actions per i dettagli. Potrebbe essere necessario un intervento manuale per recuperare le modifiche e unirle.",
                to_email=_receiver_email,
                sender_email=_sender_email
            )
    else:
        print("Task fallito o BP non aggiornato. Nessun push o PR effettuata.")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Fallito: {task_description[:50]}...",
            body=f"Il Project-Bot non è riuscito a completare il task:\n'{task_description}'.\n\nControlla i log di GitHub Actions per i dettagli.",
            to_email=_receiver_email,
            sender_email=_sender_email
        )

    print("Fine esecuzione run_project_bot.")

if __name__ == "__main__":
    pass