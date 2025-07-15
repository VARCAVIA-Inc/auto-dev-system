import os
import openai
from src.utils.email_sender import send_email
import yaml
from git import Repo, exc
from urllib.parse import urlparse, urlunparse

# --- Variabili Globali e Inizializzazione ---
_openai_api_key = None
_receiver_email = None
_sender_email = None
_github_token = None
_github_user = "VARCAVIA-Git" 

def init_project_bot_env(openai_api_key, receiver_email, sender_email, github_token):
    global _openai_api_key, _receiver_email, _sender_email, _github_token
    _openai_api_key = openai_api_key
    _receiver_email = receiver_email
    _sender_email = sender_email
    _github_token = github_token
    openai.api_key = openai_api_key
    print("Project-Bot Environment Inizializzato.")

def get_repo_root():
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

# --- Funzioni di Supporto (Git, AI) ---

def push_changes_to_main(repo_path, commit_message):
    """
    Esegue il push delle modifiche (es. nuovi piani, status aggiornati) al branch main.
    """
    if not _github_token:
        print("Errore: GITHUB_TOKEN non inizializzato. Impossibile pushare.")
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
        auth_url = urlunparse(parsed_url._replace(netloc=f"{_github_user}:{_github_token}@{netloc_part}"))
        
        repo.git.push(auth_url, "main")
        print("Modifiche pushat-e con successo al branch 'main'.")
        return True
    except Exception as e:
        print(f"Errore durante il push delle modifiche: {e}")
        # Aggiungere invio email di errore se necessario
        return False

def generate_response_with_ai(prompt, model="gpt-4o"):
    """
    Genera una risposta usando l'API di OpenAI.
    """
    if not _openai_api_key:
        print("Errore: OPENAI_API_KEY non configurata.")
        return None
    
    try:
        completion = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Sei un senior software architect e project manager. Il tuo compito è creare piani di sviluppo chiari, dettagliati e suddivisi in passi tecnici per un team di bot sviluppatori."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Errore durante la chiamata OpenAI: {e}")
        return None

def update_business_plan_status(task_index, phase_index, new_status="planned"):
    """
    Aggiorna lo stato di un task nel business_plan.yaml. Il nuovo stato di default è "planned".
    """
    repo_root = get_repo_root()
    business_plan_path = os.path.join(repo_root, 'src', 'business_plan.yaml')
    try:
        with open(business_plan_path, 'r') as file:
            plan = yaml.safe_load(file)

        plan['phases'][phase_index]['tasks'][task_index]['status'] = new_status
        
        with open(business_plan_path, 'w') as file:
            yaml.dump(plan, file, default_flow_style=False, sort_keys=False)

        print(f"Stato del task aggiornato a '{new_status}' nel business plan.")
        return True
    except Exception as e:
        print(f"Errore durante l'aggiornamento del Business Plan: {e}")
        return False

# --- LOGICA PRINCIPALE DEL BOT (FASE 1) ---

def run_project_bot(task_details, task_index, phase_index):
    """
    Funzione principale del Project_Bot per la Fase 1.
    Riceve un task e genera un piano di sviluppo dettagliato.
    """
    task_description = task_details.get('description', 'N/A')
    print(f"Inizio FASE 1: Pianificazione per il task: '{task_description}'")

    # 1. Creare il prompt per la pianificazione
    prompt_per_piano = (
        f"Dato l'obiettivo di alto livello: '{task_description}', crea un piano di sviluppo tecnico dettagliato. "
        "Il piano deve essere in formato Markdown con una checklist di sotto-task. "
        "Ogni sotto-task deve essere chiaro, specifico e implementabile da un bot sviluppatore. "
        "Includi i file da creare, le funzioni da definire e i test da scrivere. "
        "Inizia il piano con un titolo '# Piano di Sviluppo'."
    )

    # 2. Generare il piano di sviluppo con l'AI
    print("Sto generando il piano di sviluppo con l'AI...")
    piano_generato = generate_response_with_ai(prompt_per_piano)

    if not piano_generato:
        print("Fallimento nella generazione del piano. Interruzione del task.")
        update_business_plan_status(task_index, phase_index, "planning_failed")
        # Qui potremmo anche committare lo stato di fallimento
        return

    print("Piano di sviluppo generato con successo.")

    # 3. Salvare il piano in un nuovo file
    repo_root = get_repo_root()
    plan_path = os.path.join(repo_root, 'development_plan.md')
    try:
        with open(plan_path, 'w') as f:
            f.write(piano_generato)
        print(f"Piano di sviluppo salvato in '{plan_path}'")
    except Exception as e:
        print(f"Impossibile salvare il piano di sviluppo: {e}")
        return

    # 4. Aggiornare lo stato del task principale a "planned"
    update_business_plan_status(task_index, phase_index, "planned")
    
    # 5. Committare e pushare il nuovo piano e lo stato aggiornato del business plan
    commit_message = f"feat: Generato piano di sviluppo per '{task_description}'"
    push_changes_to_main(repo_root, commit_message)

    print(f"FASE 1 completata per il task: '{task_description}'.")
