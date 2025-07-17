# src/project_bot.py
import os
import yaml
import google.generativeai as genai
import subprocess
from src.utils.git_utils import push_changes_to_main

def init_project_bot_env(github_token):
    os.environ['GITHUB_TOKEN'] = github_token
    os.environ['GITHUB_USER'] = "VARCAVIA-Git"
    print("Project-Bot Environment Inizializzato.")

def get_repo_root():
    return os.getenv('GITHUB_WORKSPACE', os.getcwd())

def generate_response_with_ai(prompt, model="gemini-1.5-pro-latest"):
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY non trovata nell'ambiente del Project Bot.")
        
        genai.configure(api_key=api_key)
        
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
    task_description = task_details.get('description', 'N/A')
    print(f"Inizio FASE 1: Pianificazione per il task: '{task_description}'")
    
    repo_root = get_repo_root()
    try:
        result = subprocess.run(['ls', '-R'], cwd=repo_root, capture_output=True, text=True)
        file_structure = result.stdout
    except Exception as e:
        file_structure = f"Impossibile leggere la struttura dei file: {e}"
    
    # MODIFICA: Regola critica aggiunta al prompt per comandi shell puliti.
    prompt_per_piano = (
        f"Considerando la seguente struttura di file e cartelle già esistente nel progetto:\n"
        f"```\n{file_structure}\n```\n\n"
        f"Crea un piano di sviluppo tecnico dettagliato in Markdown per l'obiettivo: '{task_description}'.\n"
        f"**REGOLE FONDAMENTALI:**\n"
        f"1. **NON** creare file o cartelle che esistono già.\n"
        f"2. Ogni sotto-task che modifica o crea un file DEVE iniziare con il percorso del file tra parentesi quadre. Esempio: '- [ ] [src/calculator.py] Definire la classe Calculator'.\n"
        f"3. Se un task è un'azione generica, usa '[shell-command]'.\n"
        f"4. **REGOLA CRITICA**: Per i task di tipo '[shell-command]', il testo che segue DEVE essere **SOLO ED ESCLUSIVAMENTE** il comando puro, valido ed eseguibile. NON includere commenti, spiegazioni o backtick. Esempio CORRETTO: '- [ ] [shell-command] mkdir -p docs'. Esempio ERRATO: '- [ ] [shell-command] `mkdir docs` (crea la cartella)'."
    )
    
    print("Sto generando il piano di sviluppo con Gemini (con nuove regole)...")
    piano_generato = generate_response_with_ai(prompt_per_piano)
    if not piano_generato:
        print("Fallimento nella generazione del piano."); 
        update_business_plan_status(task_index, phase_index, "planning_failed")
        return
        
    print("Piano di sviluppo generato.")
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