import os
import openai
from src.utils.email_sender import send_email
import yaml
# Rimuovi importazioni GitPython e PyGithubClient
# from git import Repo, exc
# from github import Github as PyGithubClient
# from urllib.parse import urlparse, urlunparse

# Variabili Globali per le credenziali
_openai_api_key = None
_receiver_email = None
_sender_email = None
_github_token = None # Ancora passato, utile se ci fossero chiamate PyGithub dirette in futuro
# _github_api_client = None # Non più necessario per questo file

def init_project_bot_env(openai_api_key, receiver_email, sender_email, github_token):
    """
    Inizializza le variabili d'ambiente per il Project-Bot.
    """
    global _openai_api_key, _receiver_email, _sender_email, _github_token
    _openai_api_key = openai_api_key
    _receiver_email = receiver_email
    _sender_email = sender_email
    _github_token = github_token # Conserva il token per uso futuro se necessario, ma non per Git/PR qui
    openai.api_key = openai_api_key
    print("Project-Bot Environment Inizializzato.")
    # Rimuovi inizializzazione PyGithub client da qui, sarà nel nuovo workflow
    # if not _github_api_client:
    # try:
    #    _github_api_client = PyGithubClient(_github_token)
    #    print("PyGithub client inizializzato.")
    # except Exception as e:
    #    print(f"Errore nell'inizializzazione del client PyGithub: {e}")
    #    send_email(...)
    #    _github_api_client = None


# Rimuovi tutte le funzioni relative a GitPython e PyGithubClient
# def get_repo_obj(): ...
# def commit_and_push_on_new_branch(...): ...

# Funzioni ausiliarie
def get_repo_root():
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

# Funzioni principali del Project-Bot (quasi tutte rimangono uguali)
def generate_response_with_ai(prompt, model="gpt-4o-mini"):
    """
    Genera una risposta usando l'API di OpenAI.
    """
    global _openai_api_key 
    if not _openai_api_key:
        print("Errore: OPENAI_API_KEY non configurata per la chiamata AI. Impossibile generare contenuto.")
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore Configurazione OpenAI",
            body="Il Project-Bot non ha trovato la OPENAI_API_KEY. Assicurati che sia configurata correttamente nei Secrets.",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return None
    
    print(f"DEBUG: Tentativo di chiamata OpenAI API. Prompt: {prompt[:100]}...")
    
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
    except openai.AuthenticationError as e:
        print(f"Errore di autenticazione OpenAI: {e}. Controlla la OPENAI_API_KEY.")
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore di Autenticazione OpenAI",
            body=f"Il Project-Bot ha riscontrato un errore di autenticazione con l'API di OpenAI.\nErrore: {e}\nAssicurati che OPENAI_API_KEY sia corretta e valida.",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return None
    except openai.APICallError as e:
        print(f"Errore durante la chiamata API OpenAI: {e}. Code: {e.code}, Type: {e.type}")
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore API OpenAI",
            body=f"Il Project-Bot ha riscontrato un errore durante la chiamata API di OpenAI.\nErrore: {e}\nCode: {e.code}, Type: {e.type}",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        return None
    except Exception as e:
        print(f"Errore generico durante la chiamata OpenAI: {e}. Tipo: {type(e)}")
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
        try:
            ai_generated_content = generate_response_with_ai(prompt_for_content)
        except Exception as e:
            print(f"Errore inaspettato durante la chiamata generate_response_with_ai: {e}")
            ai_generated_content = None
        
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
    """
    Aggiorna lo stato di un task nel business_plan.yaml (solo localmente).
    """
    global _receiver_email, _sender_email 
    repo_root = get_repo_root()
    business_plan_path = os.path.join(repo_root, 'src', 'business_plan.yaml')

    print(f"Tentativo di aggiornare BP localmente per task {task_index} fase {phase_index} a {new_status}")

    try:
        with open(business_plan_path, 'r') as file:
            plan = yaml.safe_load(file)

        if plan and 'phases' in plan and len(plan['phases']) > phase_index and \
           'tasks' in plan['phases'][phase_index] and \
           len(plan['phases'][phase_index]['tasks']) > task_index:
            
            plan['phases'][phase_index]['tasks'][task_index]['status'] = new_status
            
            with open(business_plan_path, 'w') as file:
                yaml.dump(plan, file, default_flow_style=False, sort_keys=False)

            print(f"Stato del task {task_index} nella fase {phase_index} aggiornato a '{new_status}' localmente.")
            return True
        else:
            print("Avviso: Impossibile trovare il task da aggiornare nel Business Plan (nella scrittura locale).")
            return False

    except Exception as e:
        print(f"Errore durante l'aggiornamento del Business Plan (solo scrittura file): {e}. Tipo: {type(e)}") # <--- DEBUG TYPE
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore Project-Bot: Aggiornamento Business Plan (solo scrittura) fallito",
            body=f"Il Project-Bot non è riuscito a scrivere il business_plan.yaml dopo l'aggiornamento dello stato.\nErrore: {e}\nTipo: {type(e)}",
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
    print(f"Task details completi: {task_details}")
    
    task_completed = False
    commit_message = f"feat: {task_description[:70]}..."

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
        task_completed = False # Considera il task fallito se non si può aggiornare il BP

    # 3. Scrivi un file di trigger per il workflow di push/PR (solo se task completato e BP aggiornato)
    if task_completed and bp_update_successful:
        print("Task completato e BP aggiornato localmente. Creazione file di trigger per il workflow Git/PR.")
        trigger_file_path = os.path.join(get_repo_root(), ".autodev-trigger")
        try:
            with open(trigger_file_path, 'w') as f:
                f.write(f"task_status: {'completed'}\n")
                f.write(f"commit_message: {commit_message}\n")
                f.write(f"timestamp: {os.getenv('GITHUB_RUN_ID')}\n")
            print(f"File di trigger '{trigger_file_path}' creato con successo.")
            
            send_email(
                subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Completato Localmente: {task_description[:50]}...",
                body=f"Il Project-Bot ha completato il task:\n'{task_description}'\n\nIl Business Plan è stato aggiornato localmente e il file di trigger per il workflow Git/PR è stato creato. Attendi la Pull Request.",
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
            task_completed = False # Considera il task fallito se non può triggerare la fase successiva
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