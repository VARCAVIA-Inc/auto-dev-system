import os
import openai
from src.utils.email_sender import send_email
import yaml
from git import Repo, exc
from urllib.parse import urlparse, urlunparse

# --- Inizializzazione (Queste verranno passate, non lette da env qui) ---
#openai.api_key = os.getenv("OPENAI_API_KEY") # Rimuovi o commenta questa riga
#RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL") # Rimuovi o commenta questa riga
#SENDER_EMAIL = os.getenv("SENDER_EMAIL")     # Rimuovi o commenta questa riga
#GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY") # Rimuovi o commenta questa riga
#GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")       # Rimuovi o commenta questa riga

# --- Variabili Globali per l'API Key (verrà impostata quando la funzione viene chiamata) ---
_openai_api_key = None
_receiver_email = None
_sender_email = None
_github_token = None # Usato per GitPython

def init_project_bot_env(openai_api_key, receiver_email, sender_email, github_token):
    """
    Inizializza le variabili d'ambiente per il Project-Bot.
    Questa funzione deve essere chiamata prima di run_project_bot.
    """
    global _openai_api_key, _receiver_email, _sender_email, _github_token
    _openai_api_key = openai_api_key
    _receiver_email = receiver_email
    _sender_email = sender_email
    _github_token = github_token
    openai.api_key = openai_api_key # Imposta la chiave API di OpenAI

# Funzioni ausiliarie per la gestione del repository Git
def get_repo_root():
    """Restituisce il percorso della radice del repository."""
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

def commit_and_push_changes(repo_path, commit_message, file_paths=None):
    """Committa e pusha le modifiche al repository."""
    global _github_token # <--- Usa la variabile globale
    if not _github_token:
        print("Errore: GITHUB_TOKEN non inizializzato per il commit/push.")
        return False

    try:
        repo = Repo(repo_path)
        
        if file_paths:
            repo.index.add(file_paths)
        else:
            repo.git.add(all=True)

        if not repo.index.diff("HEAD"):
            print("Nessuna modifica da committare.")
            return True

        repo.index.commit(commit_message)
        
        origin = repo.remote(name='origin')
        original_url = origin.url
        parsed_url = urlparse(original_url)
        
        netloc_with_token = f"oauth2:{_github_token}@github.com" # <--- Usa _github_token
        if '@' in parsed_url.netloc:
            netloc_with_token += parsed_url.netloc.split('@', 1)[1]
        else:
            netloc_with_token += parsed_url.netloc

        auth_url = urlunparse(parsed_url._replace(netloc=netloc_with_token))
        
        repo.git.remote('set-url', 'origin', auth_url)
        
        current_branch = repo.active_branch.name
        origin.push(current_branch)
        
        repo.git.remote('set-url', 'origin', original_url)
        
        print(f"Modifiche committate e pushati al branch '{current_branch}' con successo.")
        return True
    except exc.GitCommandError as e:
        print(f"Errore Git: {e}")
        send_email( # <--- Usa _receiver_email e _sender_email
            subject=f"[AUTO-DEV-SYSTEM] Errore Git nel Project-Bot",
            body=f"Il Project-Bot ha riscontrato un errore Git durante commit/push.\nErrore: {e}\nMessaggio: {commit_message}",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return False
    except Exception as e:
        print(f"Errore generico durante commit/push: {e}")
        send_email( # <--- Usa _receiver_email e _sender_email
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
    global _openai_api_key # <--- Usa la variabile globale
    if not _openai_api_key:
        print("Errore: OPENAI_API_KEY non configurata.")
        return None
    try:
        # Assumi che openai.api_key sia già impostata da init_project_bot_env
        completion = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Sei un assistente AI utile e specializzato nella generazione di codice e contenuti tecnici."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except openai.APIError as e:
        print(f"Errore API OpenAI: {e}")
        send_email( # <--- Usa _receiver_email e _sender_email
            subject="[AUTO-DEV-SYSTEM] Errore API OpenAI",
            body=f"Il Project-Bot ha riscontrato un errore con l'API di OpenAI.\nErrore: {e}",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return None
    except Exception as e:
        print(f"Errore generico durante la chiamata OpenAI: {e}")
        send_email( # <--- Usa _receiver_email e _sender_email
            subject="[AUTO-DEV-SYSTEM] Errore Project-Bot (OpenAI)",
            body=f"Il Project-Bot ha riscontrato un errore generico durante la chiamata OpenAI.\nErrore: {e}",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return None

def create_file_task(task_details):
    # ... (questa funzione rimane uguale) ...
    pass

def update_business_plan_status(task_index, phase_index, new_status="completed"):
    # ... (questa funzione rimane uguale) ...
    pass

def run_project_bot(task_details, task_index, phase_index):
    """
    Funzione principale del Project-Bot.
    Prende i dettagli del task e li elabora.
    """
    global _receiver_email, _sender_email # <--- Rendi globali per send_email
    task_description = task_details.get('description', 'N/A')
    task_type = task_details.get('type')
    
    print(f"Project-Bot avviato per il task '{task_description}' (Tipo: {task_type}).")
    
    task_completed = False

    if task_type == 'create_file':
        task_completed = create_file_task(task_details)
    elif task_type == 'info' or task_type == 'action' or task_type == 'generate_code':
        ai_prompt = f"Genera un messaggio per il completamento del seguente task: '{task_description}'."
        ai_response = generate_response_with_ai(ai_prompt)
        if ai_response:
            print(f"Risposta AI per il task '{task_description}': {ai_response}")
            send_email( # <--- Usa _receiver_email e _sender_email
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
        send_email( # <--- Usa _receiver_email e _sender_email
            subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Sconosciuto: {task_description[:50]}...",
            body=f"Il Project-Bot ha incontrato un task con tipo sconosciuto: '{task_type}' per la descrizione: '{task_description}'.",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        task_completed = False

    if task_completed:
        update_business_plan_status(task_index, phase_index, "completed")
        send_email( # <--- Usa _receiver_email e _sender_email
            subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Completato: {task_description[:50]}...",
            body=f"Il Project-Bot ha completato con successo il task:\n'{task_description}'",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
    else:
        update_business_plan_status(task_index, phase_index, "failed")
        send_email( # <--- Usa _receiver_email e _sender_email
            subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Fallito: {task_description[:50]}...",
            body=f"Il Project-Bot non è riuscito a completare il task:\n'{task_description}'",
            to_email=_receiver_email,
            sender_email=_sender_email
        )

    print("Project-Bot completato per questa esecuzione.")

if __name__ == "__main__":
    # In un ambiente di test diretto, potresti impostare queste variabili per i test
    os.environ["OPENAI_API_KEY"] = "sk-..." # SOLO PER TEST LOCALE
    os.environ["RECEIVER_EMAIL"] = "code@varcavia.com"
    os.environ["SENDER_EMAIL"] = "workspace@varcavia.com"
    os.environ["GITHUB_TOKEN"] = "github_pat_..." # SOLO PER TEST LOCALE

    init_project_bot_env(
        os.getenv("OPENAI_API_KEY"),
        os.getenv("RECEIVER_EMAIL"),
        os.getenv("SENDER_EMAIL"),
        os.getenv("GITHUB_TOKEN")
    )
    print("Esecuzione diretta del Project-Bot (solo per test).")
    run_project_bot({"description": "Crea una funzione Python per calcolare il fattoriale di un numero.", "type": "generate_code"}, 0, 0)