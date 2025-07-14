import os
import openai
from src.utils.email_sender import send_email
import yaml
from git import Repo, exc
from urllib.parse import urlparse, urlunparse # Questa riga può rimanere, non danneggia

# Variabili Globali per le credenziali (verranno impostate da init_project_bot_env)
_openai_api_key = None
_receiver_email = None
_sender_email = None
_github_token = None # Questo sarà il GITHUB_TOKEN implicito del workflow

def init_project_bot_env(openai_api_key, receiver_email, sender_email, github_token):
    """
    Inizializza le variabili d'ambiente per il Project-Bot.
    Questa funzione deve essere chiamata dal Manager-Bot prima di run_project_bot.
    """
    global _openai_api_key, _receiver_email, _sender_email, _github_token
    _openai_api_key = openai_api_key
    _receiver_email = receiver_email
    _sender_email = sender_email
    _github_token = github_token # Salviamo il token (anche se per il push non lo useremo direttamente qui)
    openai.api_key = openai_api_key # Imposta la chiave API di OpenAI per il client
    print("Project-Bot Environment Inizializzato.")

# Funzioni ausiliarie per la gestione del repository Git
def get_repo_root():
    """Restituisce il percorso della radice del repository."""
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

def commit_and_push_changes(repo_path, commit_message, file_paths=None):
    """Committa e pusha le modifiche al repository."""
    # Il _github_token sarà passato, ma il push farà affidamento sull'ambiente di Actions.
    # Non useremo più il _github_token esplicitamente per impostare l'URL qui.
    
    print(f"Tentativo di commit e push: '{commit_message}'")
    # Il log del token non è più rilevante qui dato che ci affidiamo all'ambiente
    # print(f"Token usato per push: {'*****' if _github_token else 'Nessun token'}")

    try:
        repo = Repo(repo_path)
        
        # Se non specificati, aggiunge tutti i file modificati/nuovi
        if file_paths:
            repo.index.add(file_paths)
        else:
            repo.git.add(all=True) # Aggiunge tutte le modifiche

        if not repo.index.diff("HEAD"): # Controlla se ci sono modifiche da committare
            print("Nessuna modifica da committare.")
            return True

        repo.index.commit(commit_message)
        
        # --- INIZIO MODIFICA CRITICA: Semplificazione del push ---
        # NON impostiamo più l'URL remoto con il token esplicito.
        # Ci affidiamo al fatto che actions/checkout@v4 configura Git per usare GITHUB_TOKEN implicito.
        origin = repo.remote(name='origin')
        
        current_branch = repo.active_branch.name
        print(f"Pushing al branch: {current_branch} usando l'autenticazione implicita di GitHub Actions.")
        origin.push(current_branch) # Questo dovrebbe usare il GITHUB_TOKEN del workflow
        
        # Non è necessario ripristinare l'URL, dato che non lo abbiamo modificato.
        # --- FINE MODIFICA CRITICA ---
        
        print(f"Modifiche committate e pushati al branch '{current_branch}' con successo.")
        return True
    except exc.GitCommandError as e:
        print(f"Errore Git: {e}")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Errore Git nel Project-Bot",
            body=f"Il Project-Bot ha riscontrato un errore Git durante commit/push.\nErrore: {e}\nMessaggio: {commit_message}",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return False
    except Exception as e:
        print(f"Errore generico durante commit/push: {e}")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Errore generico nel Project-Bot (Git)",
            body=f"Il Project-Bot ha riscontrato un errore generico durante commit/push.\nErrore: {e}\nMessaggio: {commit_message}",
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
    print(f"Chiamata OpenAI API con prompt: {prompt[:100]}...")
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
    except openai.APIError as e:
        print(f"Errore API OpenAI: {e}")
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore API OpenAI",
            body=f"Il Project-Bot ha riscontrato un errore con l'API di OpenAI.\nErrore: {e}",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return None
    except Exception as e:
        print(f"Errore generico durante la chiamata OpenAI: {e}")
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore Project-Bot (OpenAI)",
            body=f"Il Project-Bot ha riscontrato un errore generico durante la chiamata OpenAI.\nErrore: {e}",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return None

def create_file_task(task_details):
    """
    Gestisce il task di creazione di un file.
    """
    file_path = task_details.get('path')
    prompt_for_content = task_details.get('prompt_for_content')

    if not file_path:
        print("Errore: 'path' non specificato per il task 'create_file'.")
        return False

    print(f"Tentativo di creazione file: {file_path}")
    content = ""
    if prompt_for_content:
        print(f"Generando contenuto AI per il file: {file_path}...")
        ai_generated_content = generate_response_with_ai(prompt_for_content)
        if ai_generated_content:
            content = ai_generated_content
        else:
            print("Impossibile generare contenuto AI. Il file non verrà creato.")
            return False

    try:
        dir_name = os.path.dirname(file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        
        full_path = os.path.join(get_repo_root(), file_path) # Assicurati che il percorso sia relativo alla root del repo
        with open(full_path, 'w') as f:
            f.write(content)
        print(f"File '{full_path}' creato/aggiornato con successo.")
        return True
    except Exception as e:
        print(f"Errore durante la creazione del file '{file_path}': {e}")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Errore Project-Bot: Creazione file fallita",
            body=f"Il Project-Bot non è riuscito a creare il file '{file_path}'.\nErrore: {e}",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return False

def update_business_plan_status(task_index, phase_index, new_status="completed"):
    """
    Aggiorna lo stato di un task nel business_plan.yaml e pusha la modifica.
    """
    global _receiver_email, _sender_email # Ensure these are global
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

            commit_message = f"chore: Update business plan - task {task_index} in phase {phase_index} set to {new_status}"
            return commit_and_push_changes(repo_root, commit_message, file_paths=[business_plan_path])
        else:
            print("Avviso: Impossibile trovare il task da aggiornare nel Business Plan.")
            return False

    except Exception as e:
        print(f"Errore durante l'aggiornamento del Business Plan: {e}")
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore Project-Bot: Aggiornamento Business Plan fallito",
            body=f"Il Project-Bot non è riuscito ad aggiornare il business_plan.yaml.\nErrore: {e}",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return False

def run_project_bot(task_details, task_index, phase_index):
    """
    Funzione principale del Project-Bot.
    Prende i dettagli del task e li elabora.
    """
    global _receiver_email, _sender_email # Assicurati che queste siano globali per send_email
    task_description = task_details.get('description', 'N/A')
    task_type = task_details.get('type')
    
    print(f"Inizio esecuzione run_project_bot per task: '{task_description}' (Tipo: {task_type}).")
    
    task_completed = False

    if task_type == 'create_file':
        task_completed = create_file_task(task_details)
    elif task_type == 'info' or task_type == 'action' or task_type == 'generate_code':
        ai_prompt = f"Genera un messaggio per il completamento del seguente task: '{task_description}'."
        ai_response = generate_response_with_ai(ai_prompt)
        if ai_response:
            print(f"Risposta AI per il task '{task_description}': {ai_response}")
            send_email(
                subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Info/Action: {task_description[:50]}...",
                body=f"Il Project-Bot ha elaborato il task:\n'{task_description}'\n\nRisposta AI:\n{ai_response}",
                to_email=_receiver_email,
                sender_email=_sender_email
            )
            task_completed = True
        else:
            print("Il Project-Bot non è riuscito a generare una risposta AI per il task info/action.")
            task_completed = False
    else:
        print(f"Tipo di task sconosciuto: {task_type}. Nessuna azione specifica.")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Sconosciuto: {task_description[:50]}...",
            body=f"Il Project-Bot ha incontrato un task con tipo sconosciuto: '{task_type}' per la descrizione: '{task_description}'.",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        task_completed = False

    # Logica di notifica finale e aggiornamento BP
    if task_completed:
        print("Task completato con successo. Tentativo di aggiornare Business Plan e inviare email di conferma.")
        if update_business_plan_status(task_index, phase_index, "completed"):
             send_email(
                subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Completato: {task_description[:50]}...",
                body=f"Il Project-Bot ha completato con successo il task:\n'{task_description}'\n\nIl Business Plan è stato aggiornato.",
                to_email=_receiver_email,
                sender_email=_sender_email
            )
        else:
            print("Avviso: Task completato, ma aggiornamento Business Plan o push fallito.")
            send_email(
                subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Completato (Problemi Aggiornamento BP): {task_description[:50]}...",
                body=f"Il Project-Bot ha completato il task:\n'{task_description}'\n\nMA non è riuscito ad aggiornare il Business Plan o a pushare le modifiche. Controllare i log.",
                to_email=_receiver_email,
                sender_email=_sender_email
            )
    else:
        print("Task fallito. Tentativo di aggiornare Business Plan e inviare email di notifica fallimento.")
        if update_business_plan_status(task_index, phase_index, "failed"):
            send_email(
                subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Fallito: {task_description[:50]}...",
                body=f"Il Project-Bot non è riuscito a completare il task:\n'{task_description}'\n\nIl Business Plan è stato aggiornato.",
                to_email=_receiver_email,
                sender_email=_sender_email
            )
        else:
            print("Avviso: Task fallito, e aggiornamento Business Plan o push fallito.")
            send_email(
                subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Fallito (Problemi Aggiornamento BP): {task_description[:50]}...",
                body=f"Il Project-Bot non è riuscito a completare il task:\n'{task_description}'\n\nE non è riuscito ad aggiornare il Business Plan o a pushare le modifiche. Controllare i log.",
                to_email=_receiver_email,
                sender_email=_sender_email
            )

    print("Fine esecuzione run_project_bot.")

if __name__ == "__main__":
    pass # Non usiamo più il blocco di test diretto qui.