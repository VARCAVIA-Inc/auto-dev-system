import os
import openai
from src.utils.email_sender import send_email
import yaml
from git import Repo, exc # Importa la libreria GitPython

# Inizializza il client OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") # Necessario per il push con GitPython

# Funzioni ausiliarie per la gestione del repository Git
def get_repo_root():
    """Restituisce il percorso della radice del repository."""
    # In GitHub Actions, GITHUB_WORKSPACE è la radice del repo
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

        if repo.index.diff("HEAD"): # Controlla se ci sono modifiche da committare
            repo.index.commit(commit_message)
            # Configura le credenziali per il push
            remote_url = repo.remote().url
            # Sostituisci "https://" con "https://oauth2:${GITHUB_TOKEN}@" per autenticazione
            if "https://" in remote_url and "github.com" in remote_url:
                push_url = remote_url.replace("https://", f"https://oauth2:{GITHUB_TOKEN}@")
            else: # Per altri tipi di URL o se già con username/token
                push_url = remote_url
            
            # Non usare 'main' staticamente, usa il branch corrente
            current_branch = repo.active_branch.name

            origin = repo.remote(name='origin')
            with origin.custom_url_evaluator(lambda url: push_url):
                origin.push(current_branch)
            print(f"Modifiche committate e pushati al branch '{current_branch}' con successo.")
            return True
        else:
            print("Nessuna modifica da committare.")
            return True
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
    """
    Genera una risposta usando l'API di OpenAI.
    """
    if not openai.api_key:
        print("Errore: OPENAI_API_KEY non configurata.")
        return None
    try:
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
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore API OpenAI",
            body=f"Il Project-Bot ha riscontrato un errore con l'API di OpenAI.\nErrore: {e}",
            to_email=RECEIVER_EMAIL,
            sender_email=SENDER_EMAIL
        )
        return None
    except Exception as e:
        print(f"Errore generico durante la chiamata OpenAI: {e}")
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore Project-Bot (OpenAI)",
            body=f"Il Project-Bot ha riscontrato un errore generico durante la chiamata OpenAI.\nErrore: {e}",
            to_email=RECEIVER_EMAIL,
            sender_email=SENDER_EMAIL
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

    content = ""
    if prompt_for_content:
        print(f"Generando contenuto AI per il file: {file_path}...")
        ai_generated_content = generate_response_with_ai(prompt_for_content)
        if ai_generated_content:
            content = ai_generated_content
        else:
            print("Impossibile generare contenuto AI. Il file verrà creato vuoto.")
            return False # Fallisce se la generazione AI fallisce e il contenuto era richiesto

    try:
        # Crea le directory se non esistono
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
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
    """
    Aggiorna lo stato di un task nel business_plan.yaml e pusha la modifica.
    """
    repo_root = get_repo_root()
    business_plan_path = os.path.join(repo_root, 'src', 'business_plan.yaml')

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
            # Il commit_and_push_changes gestirà l'aggiunta specifica del file
            return commit_and_push_changes(repo_root, commit_message, file_paths=[business_plan_path])
        else:
            print("Avviso: Impossibile trovare il task da aggiornare nel Business Plan.")
            return False

    except Exception as e:
        print(f"Errore durante l'aggiornamento del Business Plan: {e}")
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore Project-Bot: Aggiornamento Business Plan fallito",
            body=f"Il Project-Bot non è riuscito ad aggiornare il business_plan.yaml.\nErrore: {e}",
            to_email=RECEIVER_EMAIL,
            sender_email=SENDER_EMAIL
        )
        return False

def run_project_bot(task_details, task_index, phase_index):
    """
    Funzione principale del Project-Bot.
    Prende i dettagli del task e li elabora.
    """
    task_description = task_details.get('description', 'N/A')
    task_type = task_details.get('type')
    
    print(f"Project-Bot avviato per il task '{task_description}' (Tipo: {task_type}).")
    
    task_completed = False

    if task_type == 'create_file':
        task_completed = create_file_task(task_details)
    elif task_type == 'info' or task_type == 'action' or task_type == 'generate_code':
        # Per ora, questi tipi sono solo log (simulazione)
        ai_prompt = f"Genera un messaggio per il completamento del seguente task: '{task_description}'."
        ai_response = generate_response_with_ai(ai_prompt)
        if ai_response:
            print(f"Risposta AI per il task '{task_description}': {ai_response}")
            send_email(
                subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Info/Action: {task_description[:50]}...",
                body=f"Il Project-Bot ha elaborato il task:\n'{task_description}'\n\nRisposta AI:\n{ai_response}",
                to_email=RECEIVER_EMAIL,
                sender_email=SENDER_EMAIL
            )
            task_completed = True # Considera completato per questi tipi semplici
        else:
            print("Il Project-Bot non è riuscito a generare una risposta AI per il task info/action.")
            task_completed = False
    else:
        print(f"Tipo di task sconosciuto: {task_type}. Nessuna azione specifica.")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Sconosciuto: {task_description[:50]}...",
            body=f"Il Project-Bot ha incontrato un task con tipo sconosciuto: '{task_type}' per la descrizione: '{task_description}'.",
            to_email=RECEIVER_EMAIL,
            sender_email=SENDER_EMAIL
        )
        task_completed = False

    # Aggiorna lo stato del Business Plan solo se il task è stato completato
    if task_completed:
        update_business_plan_status(task_index, phase_index, "completed")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Completato: {task_description[:50]}...",
            body=f"Il Project-Bot ha completato con successo il task:\n'{task_description}'",
            to_email=RECEIVER_EMAIL,
            sender_email=SENDER_EMAIL
        )
    else:
        update_business_plan_status(task_index, phase_index, "failed")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Fallito: {task_description[:50]}...",
            body=f"Il Project-Bot non è riuscito a completare il task:\n'{task_description}'",
            to_email=RECEIVER_EMAIL,
            sender_email=SENDER_EMAIL
        )

    print("Project-Bot completato per questa esecuzione.")

# Il blocco if __name__ == "__main__": non verrà modificato in questo passaggio.