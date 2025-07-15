import os
import openai
import yaml
from src.utils.git_utils import push_changes_to_main

_openai_api_key = None

def init_project_bot_env(openai_api_key, receiver_email, sender_email, github_token):
    global _openai_api_key
    _openai_api_key = openai_api_key
    os.environ['GITHUB_TOKEN'] = github_token
    os.environ['GITHUB_USER'] = "VARCAVIA-Git"
    openai.api_key = openai_api_key
    print("Project-Bot Environment Inizializzato.")

def get_repo_root():
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

def generate_response_with_ai(prompt, model="gpt-4o"):
    if not _openai_api_key:
        print("Errore: OPENAI_API_KEY non configurata.")
        return None
    try:
        completion = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Sei un senior software architect. Il tuo compito è creare piani di sviluppo chiari, dettagliati e suddivisi in passi tecnici per un team di bot sviluppatori."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Errore durante la chiamata OpenAI: {e}")
        return None

def update_business_plan_status(task_index, phase_index, new_status="planned"):
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

def run_project_bot(task_details, task_index, phase_index):
    task_description = task_details.get('description', 'N/A')
    print(f"Inizio FASE 1: Pianificazione per il task: '{task_description}'")
    
    prompt_per_piano = (
        f"Dato l'obiettivo di alto livello: '{task_description}', crea un piano di sviluppo tecnico dettagliato. "
        "Il piano deve essere in formato Markdown con una checklist. "
        "Ogni sotto-task DEVE iniziare con il percorso completo del file su cui operare, racchiuso tra parentesi quadre. "
        "Esempio: '- [ ] [src/app/main.py] Creare la funzione di avvio'."
    )
    
    print("Sto generando il piano di sviluppo con l'AI...")
    piano_generato = generate_response_with_ai(prompt_per_piano)
    if not piano_generato:
        print("Fallimento nella generazione del piano. Interruzione del task.")
        update_business_plan_status(task_index, phase_index, "planning_failed")
        return
        
    print("Piano di sviluppo generato con successo.")
    repo_root = get_repo_root()
    plan_path = os.path.join(repo_root, 'development_plan.md')
    try:
        with open(plan_path, 'w') as f:
            f.write(piano_generato)
        print(f"Piano di sviluppo salvato in '{plan_path}'")
    except Exception as e:
        print(f"Impossibile salvare il piano di sviluppo: {e}")
        return
        
    update_business_plan_status(task_index, phase_index, "planned")
    commit_message = f"feat: Generato piano di sviluppo per '{task_description}'"
    push_changes_to_main(repo_root, commit_message)
    print(f"FASE 1 completata per il task: '{task_description}'.")