import os
import yaml
import google.generativeai as genai
from src.utils.git_utils import push_changes_to_main

_gemini_api_key = None

def init_project_bot_env(openai_api_key, receiver_email, sender_email, github_token):
    # Questa funzione ora gestirà la chiave Gemini passata dal manager
    global _gemini_api_key
    _gemini_api_key = os.getenv("GEMINI_API_KEY") # Leggiamo la nuova variabile
    os.environ['GITHUB_TOKEN'] = github_token
    os.environ['GITHUB_USER'] = "VARCAVIA-Git"
    if _gemini_api_key:
        genai.configure(api_key=_gemini_api_key)
    print("Project-Bot Environment Inizializzato per Gemini.")

def get_repo_root():
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

def generate_response_with_ai(prompt, model="gemini-1.5-pro-latest"):
    if not _gemini_api_key:
        print("Errore: GEMINI_API_KEY non configurata.")
        return None
    try:
        gemini_model = genai.GenerativeModel(model)
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Errore durante la chiamata a Gemini: {e}")
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
        print(f"Stato del task aggiornato a '{new_status}'.")
        return True
    except Exception as e:
        print(f"Errore durante l'aggiornamento del Business Plan: {e}")
        return False

def run_project_bot(task_details, task_index, phase_index):
    # (La logica di questa funzione rimane identica, ma ora chiamerà Gemini)
    task_description = task_details.get('description', 'N/A')
    print(f"Inizio FASE 1: Pianificazione per il task: '{task_description}'")
    
    prompt_per_piano = (
        f"Dato l'obiettivo: '{task_description}', crea un piano di sviluppo tecnico dettagliato in Markdown. "
        "Ogni riga del piano deve essere un sotto-task in una checklist.\n"
        "**REGOLE FONDAMENTALI:**\n"
        "1. Ogni sotto-task che modifica o crea un file DEVE iniziare con il percorso del file tra parentesi quadre. Esempio: '- [ ] [src/calculator.py] Definire la classe Calculator'.\n"
        "2. Se un task è un'azione generica (es. creare cartelle), usa '[shell-command]' come marcatore. Esempio: '- [ ] [shell-command] mkdir -p src/app'.\n"
    )
    
    print("Sto generando il piano di sviluppo con Gemini...")
    piano_generato = generate_response_with_ai(prompt_per_piano)
    if not piano_generato:
        print("Fallimento nella generazione del piano."); update_business_plan_status(task_index, phase_index, "planning_failed"); return
        
    print("Piano di sviluppo generato.")
    repo_root = get_repo_root()
    plan_path = os.path.join(repo_root, 'development_plan.md')
    try:
        with open(plan_path, 'w') as f: f.write(piano_generato)
        print(f"Piano di sviluppo salvato in '{plan_path}'")
    except Exception as e: print(f"Impossibile salvare il piano di sviluppo: {e}"); return
        
    update_business_plan_status(task_index, phase_index, "planned")
    commit_message = f"feat: Generato piano di sviluppo (con Gemini) per '{task_description}'"
    push_changes_to_main(repo_root, commit_message)
    print(f"FASE 1 completata per il task: '{task_description}'.")