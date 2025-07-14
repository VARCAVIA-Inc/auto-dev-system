import os
import openai
from src.utils.email_sender import send_email
import yaml
from git import Repo, exc
from github import Github as PyGithubClient # Rinominato per evitare conflitto con GitPython Repo
from urllib.parse import urlparse, urlunparse

# Variabili Globali per le credenziali (verranno impostate da init_project_bot_env)
_openai_api_key = None
_receiver_email = None
_sender_email = None
_github_token = None # Questo sarà il GITHUB_TOKEN implicito del workflow
_github_api_client = None # Aggiunto client per PyGithub

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
        _github_api_client = None # Assicurati che sia None se fallisce
    
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
        return _github_api_client.get_repo(os.getenv("GITHUB_REPOSITORY"))
    except Exception as e:
        print(f"Errore nel recupero dell'oggetto repository di PyGithub: {e}")
        return None

def commit_and_push_on_new_branch(repo_path, commit_message, base_branch="main", new_branch_prefix="autodev-task-"):
    """
    Crea un nuovo branch, committa le modifiche e pusha sul nuovo branch, poi apre una PR.
    """
    global _github_token, _github_api_client, _receiver_email, _sender_email
    
    if not _github_token or not _github_api_client:
        print("Errore: Credenziali GitHub non inizializzate per commit/push/PR.")
        return False

    try:
        repo = Repo(repo_path)
        
        if not repo.index.diff("HEAD"): # Controlla se ci sono modifiche da committare
            print("Nessuna modifica da committare.")
            return True # Non ci sono modifiche da pushare, considera l'azione successa

        # 1. Crea un nuovo branch basato sul branch corrente (main)
        timestamp = os.getenv('GITHUB_RUN_ID', 'manual') # Usa Run ID per unicità
        new_branch_name = f"{new_branch_prefix}{timestamp}"
        
        # Assicurati di essere sul branch base prima di creare il nuovo branch
        repo.git.checkout(base_branch)
        new_branch = repo.create_head(new_branch_name)
        new_branch.checkout()
        print(f"Creato e passato al nuovo branch: {new_branch_name}")

        # 2. Aggiungi e committa le modifiche
        repo.git.add(all=True) # Aggiunge tutte le modifiche
        repo.index.commit(commit_message)
        print(f"Modifiche committate sul branch {new_branch_name}.")

        # 3. Push sul nuovo branch
        # Ci affidiamo al fatto che actions/checkout@v4 configura Git per usare GITHUB_TOKEN implicito.
        origin = repo.remote(name='origin')
        print(f"Pushing al branch: {new_branch_name} usando l'autenticazione implicita di GitHub Actions.")
        origin.push(new_branch_name)
        print(f"Modifiche pushati al branch '{new_branch_name}' con successo.")

        # 4. Apri una Pull Request
        repo_obj = get_repo_obj()
        if not repo_obj:
            print("Errore: Impossibile recuperare l'oggetto repository di PyGithub per creare la PR.")
            send_email(
                subject=f"[AUTO-DEV-SYSTEM] Avviso: PR non creata",
                body=f"Il Project-Bot ha completato il task e pushato le modifiche al branch '{new_branch_name}', ma non è riuscito a creare la Pull Request.",
                to_email=_receiver_email,
                sender_email=_sender_email
            )
            return False # Fallisce l'azione perché la PR non è stata creata
        
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
            body=f"Il Project-Bot ha riscontrato un errore Git durante la creazione del branch, commit o push, o PR.\nErrore: {e}\nMessaggio: {commit_message}",
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
    # ... (questa funzione rimane uguale) ...
    pass

def create_file_task(task_details):
    # ... (questa funzione rimane uguale, dato che la creazione del file funziona localmente) ...
    pass

def update_business_plan_status(task_index, phase_index, new_status="completed"):
    """
    Aggiorna lo stato di un task nel business_plan.yaml. Non pusha direttamente.
    Il push avverrà tramite commit_and_push_on_new_branch.
    """
    global _receiver_email, _sender_email 
    repo_root = get_repo_root()
    business_plan_path = os.path.join(repo_root, 'src', 'business_plan.yaml')

    print(f"Tentativo di aggiornare BP per task {task_index} fase {phase_index} a {new_status}")

    try:
        with open(business_plan_path, 'r') as file:
            plan = yaml.safe_load(file)

        if plan and 'phases' in plan and len(plan['phases']) > phase_index and \
           'tasks' in plan['phases'][phase_index] and \
           len(plan['phases'][phase_index]['tasks']) > task_index:
            
            plan['phases'][phase_index]['tasks'][task_index]['status'] = new_status
            
            with open(business_plan_path, 'w') as file:
                yaml.dump(plan, file, default_flow_style=False, sort_keys=False) # sort_keys=False mantiene l'ordine

            print(f"Stato del task {task_index} nella fase {phase_index} aggiornato a '{new_status}'.")
            return True # Non committiamo/pushiamo qui, lo farà la funzione chiamante
        else:
            print("Avviso: Impossibile trovare il task da aggiornare nel Business Plan.")
            return False

    except Exception as e:
        print(f"Errore durante l'aggiornamento del Business Plan (solo scrittura file): {e}")
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore Project-Bot: Aggiornamento Business Plan (solo scrittura) fallito",
            body=f"Il Project-Bot non è riuscito a scrivere il business_plan.yaml dopo l'aggiornamento dello stato.\nErrore: {e}",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return False

def run_project_bot(task_details, task_index, phase_index):
    """
    Funzione principale del Project-Bot.
    Prende i dettagli del task e li elabora.
    """
    global _receiver_email, _sender_email 
    task_description = task_details.get('description', 'N/A')
    task_type = task_details.get('type')
    
    print(f"Inizio esecuzione run_project_bot per task: '{task_description}' (Tipo: {task_type}).")
    
    task_completed = False
    commit_message = f"feat: {task_description[:70]}..." # Messaggio base per il commit

    # 1. Esegui l'azione del task
    if task_type == 'create_file':
        task_completed = create_file_task(task_details)
        commit_message = f"feat: Create file {task_details.get('path', 'unknown')}"
    elif task_type == 'info' or task_type == 'action' or task_type == 'generate_code':
        ai_prompt = f"Genera un messaggio per il completamento del seguente task: '{task_description}'."
        ai_response = generate_response_with_ai(ai_prompt)
        if ai_response:
            print(f"Risposta AI per il task '{task_description}': {ai_response}")
            # Non inviamo email qui, la notifica finale gestirà tutto
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
        # Se non riusciamo nemmeno a scrivere localmente, è un problema serio, non possiamo procedere al push
        task_completed = False # Considera il task fallito se non si può aggiornare il BP

    # 3. Committa e pusha le modifiche sul nuovo branch e crea PR (se ci sono modifiche)
    if task_completed and bp_update_successful: # Solo se l'azione e l'aggiornamento BP locale sono riusciti
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