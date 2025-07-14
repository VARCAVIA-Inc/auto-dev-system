import os
import openai
from src.utils.email_sender import send_email
import yaml
from git import Repo, exc # Importa la libreria GitPython
from urllib.parse import urlparse, urlunparse # <--- AGGIUNGI QUESTA RIGA PER LA MANIPOLAZIONE URL

# Inizializza il client OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Funzioni ausiliarie per la gestione del repository Git
def get_repo_root():
    """Restituisce il percorso della radice del repository."""
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

def commit_and_push_changes(repo_path, commit_message, file_paths=None):
    """Committa e pusha le modifiche al repository."""
    try:
        repo = Repo(repo_path)
        
        # Se non specificati, aggiunge tutti i file modificati/nuovi
        if file_paths:
            repo.index.add(file_paths)
        else:
            repo.git.add(all=True) # Aggiunge tutte le modifiche

        if not repo.index.diff("HEAD"): # Se non ci sono modifiche da committare, esci
            print("Nessuna modifica da committare.")
            return True

        repo.index.commit(commit_message)
        
        # --- INIZIO CORREZIONE: Gestione autenticazione GitPython ---
        # Ottieni l'URL remoto e aggiungi il token per l'autenticazione
        origin = repo.remote(name='origin')
        
        # Pulisci eventuali credenziali preesistenti nell'URL per non duplicare
        original_url = origin.url
        parsed_url = urlparse(original_url)
        
        # Ricostruisci l'URL con il token
        # Questo formato 'oauth2:TOKEN@github.com' è lo standard per i PAT su GitHub
        netloc_with_token = f"oauth2:{GITHUB_TOKEN}@github.com"
        # Se l'URL originale contiene già un utente, lo sostituiamo
        if '@' in parsed_url.netloc:
            netloc_with_token += parsed_url.netloc.split('@', 1)[1]
        else:
            netloc_with_token += parsed_url.netloc # Mantiene il dominio

        auth_url = urlunparse(parsed_url._replace(netloc=netloc_with_token))
        
        # Imposta temporaneamente l'URL del remote con il token
        # Questo comando usa il git binario sottostante direttamente
        repo.git.remote('set-url', 'origin', auth_url)
        
        # PUSHA
        current_branch = repo.active_branch.name
        origin.push(current_branch)
        
        # Ripristina l'URL originale del remote per non lasciare il token memorizzato (anche se è effimero in Action)
        repo.git.remote('set-url', 'origin', original_url)
        
        print(f"Modifiche committate e pushati al branch '{current_branch}' con successo.")
        return True
    # --- FINE CORREZIONE: Gestione autenticazione GitPython ---
    except exc.GitCommandError as e:
        print(f"Errore Git: {e}")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Errore Git nel Project-Bot",
            body=f"Il Project-Bot ha riscontrato un errore Git durante commit/push.\nErrore: {e}\nMessaggio: {commit_message}",
            to_email=RECEIVER_EMAIL,
            sender_email=SENDER_EMAIL
        )
        return False
    except Exception as e:
        print(f"Errore generico durante commit/push: {e}")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Errore generico nel Project-Bot (Git)",
            body=f"Il Project-Bot ha riscontrato un errore generico durante commit/push.\nErrore: {e}\nMessaggio: {commit_message}",
            to_email=RECEIVER_EMAIL,
            sender_email=SENDER_EMAIL
        )
        return False

# Funzioni principali del Project-Bot
def generate_response_with_ai(prompt, model="gpt-4o-mini"):
    # ... (questa funzione non cambia) ...
    pass

def create_file_task(task_details):
    """
    Gestisce il task di creazione di un file.
    """
    file_path = task_details.get('path')
    prompt_for_content = task_details.get('prompt_for_content')

    if not file_path:
        print("Errore: 'path' non specificato per il task 'create_file'.")
        return False

    content = ""
    if prompt_for_content:
        print(f"Generando contenuto AI per il file: {file_path}...")
        ai_generated_content = generate_response_with_ai(prompt_for_content)
        if ai_generated_content:
            content = ai_generated_content
        else:
            print("Impossibile generare contenuto AI. Il file verrà creato vuoto.")
            return False

    try:
        # --- INIZIO CORREZIONE: Creazione directory per file nella root ---
        dir_name = os.path.dirname(file_path)
        if dir_name: # Se c'è una directory, creala
            os.makedirs(dir_name, exist_ok=True)
        # --- FINE CORREZIONE ---
        
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"File '{file_path}' creato/aggiornato con successo.")
        return True
    except Exception as e:
        print(f"Errore durante la creazione del file '{file_path}': {e}")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Errore Project-Bot: Creazione file fallita",
            body=f"Il Project-Bot non è riuscito a creare il file '{file_path}'.\nErrore: {e}",
            to_email=RECEIVER_EMAIL,
            sender_email=SENDER_EMAIL
        )
        return False

def update_business_plan_status(task_index, phase_index, new_status="completed"):
    # ... (questa funzione non cambia nel suo comportamento, ma ora si affida alla commit_and_push_changes corretta) ...
    pass

def run_project_bot(task_details, task_index, phase_index):
    # ... (questa funzione non cambia) ...
    pass

if __name__ == "__main__":
    # ... (questa sezione non cambia) ...
    pass