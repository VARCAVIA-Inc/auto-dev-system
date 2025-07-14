import os
import yaml
from github import Github
from src.utils.email_sender import send_email
from src.project_bot import run_project_bot, init_project_bot_env # <--- AGGIUNGI init_project_bot_env

# --- Inizializzazione ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # <--- Recupera anche la chiave OpenAI qui

# Inizializza il client GitHub
try:
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(os.getenv("GITHUB_REPOSITORY"))
    print(f"Connesso al repository: {repo.full_name}")
except Exception as e:
    print(f"Errore durante l'inizializzazione di GitHub API: {e}")
    send_email(
        subject="[AUTO-DEV-SYSTEM] Errore critico: GitHub API non inizializzata",
        body=f"Il Manager-Bot non è riuscito a connettersi all'API di GitHub.\nErrore: {e}\nAssicurati che BOT_GITHUB_TOKEN sia corretto e con i permessi necessari.",
        to_email=RECEIVER_EMAIL,
        sender_email=SENDER_EMAIL
    )
    exit(1)

# --- Funzioni del Manager-Bot (non cambiano) ---
# send_initial_status_email()
# read_business_plan()

def main():
    print("Manager-Bot avviato.")

    # Inizializza l'ambiente del Project-Bot
    init_project_bot_env(OPENAI_API_KEY, RECEIVER_EMAIL, SENDER_EMAIL, GITHUB_TOKEN) # <--- AGGIUNGI QUESTA RIGA

    business_plan = read_business_plan()
    print(f"Contenuto parziale del Business Plan: {str(business_plan)[:200]}...")

    if business_plan and 'project_name' in business_plan and 'phases' in business_plan:
        print("Business Plan valido rilevato. Invocando il Project-Bot per i task...")
        
        for phase_index, phase in enumerate(business_plan['phases']):
            for task_index, task in enumerate(phase.get('tasks', [])):
                if task.get('agent') == 'ProjectBot' and task.get('status') == 'pending':
                    print(f"Trovato task pendente per ProjectBot: {task.get('description')}")
                    run_project_bot(task, task_index, phase_index)
                    print("Un task gestito. Terminando questa esecuzione del Manager-Bot.")
                    return # Esci dopo aver gestito un task

        print("Nessun task pendente trovato per ProjectBot.")
        send_email(
            subject="[AUTO-DEV-SYSTEM] Manager-Bot in attesa",
            body="Il Manager-Bot ha scansionato il Business Plan ma non ha trovato task pendenti per il Project-Bot. In attesa di nuove istruzioni.",
            to_email=RECEIVER_EMAIL,
            sender_email=SENDER_EMAIL
        )
    else:
        print("Nessun Business Plan valido o completo trovato. In attesa di istruzioni.")
        send_email(
            subject="[AUTO-DEV-SYSTEM] Manager-Bot in attesa",
            body="Il Manager-Bot non ha trovato un Business Plan valido o completo. In attesa di istruzioni.",
            to_email=RECEIVER_EMAIL,
            sender_email=SENDER_EMAIL
        )

    print("Manager-Bot completato per questa esecuzione.")

if __name__ == "__main__":
    main()