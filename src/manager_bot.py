import os
import yaml
from github import Github
from src.utils.email_sender import send_email
from src.project_bot import run_project_bot, init_project_bot_env

# --- Inizializzazione ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inizializza il client GitHub
try:
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(os.getenv("GITHUB_REPOSITORY"))
    print(f"Connesso al repository: {repo.full_name}")
except Exception as e:
    print(f"Errore durante l'inizializzazione di GitHub API: {e}")
    # In questo punto, send_email non è ancora garantito che funzioni a causa dell'inizializzazione.
    # L'Action fallirà comunque con exit(1) che è visibile nel log.
    exit(1) # Termina lo script se non si connette a GitHub

# --- Funzioni del Manager-Bot ---

def send_initial_status_email():
    """
    Invia un'email per confermare l'avvio del Manager-Bot.
    Questa funzione non viene più usata in `main()` direttamente, ma può essere utile per notifiche specifiche.
    """
    subject = "[AUTO-DEV-SYSTEM] Manager-Bot Avviato!"
    body = (
        f"Ciao {RECEIVER_EMAIL},\n\n"
        "Il Manager-Bot è stato avviato con successo e sta eseguendo il suo primo controllo.\n"
        "Questo è un test di funzionamento del sistema di notifica via email.\n\n"
        "Resto in attesa di istruzioni dal Business Plan.\n\n"
        "Saluti,\nIl tuo Manager-Bot."
    )
    print(f"Tentativo di inviare email di stato iniziale a {RECEIVER_EMAIL}...")
    success = send_email(subject, body, RECEIVER_EMAIL, SENDER_EMAIL)
    if success:
        print("Email di stato iniziale inviata.")
    else:
        print("Impossibile inviare l'email di stato iniziale.")

def read_business_plan():
    """
    Legge il file business_plan.yaml.
    """
    business_plan_path = 'src/business_plan.yaml'
    if not os.path.exists(business_plan_path):
        print(f"Avviso: Il Business Plan non trovato in {business_plan_path}. Creazione di un file vuoto.")
        with open(business_plan_path, 'w') as f:
            f.write("# Questo file conterrà il Business Plan per il tuo progetto.\n")
        return {}
    
    with open(business_plan_path, 'r') as file:
        try:
            plan = yaml.safe_load(file)
            print("Business Plan letto con successo.")
            return plan if plan else {}
        except yaml.YAMLError as exc:
            print(f"Errore durante la lettura del Business Plan: {exc}")
            send_email(
                subject="[AUTO-DEV-SYSTEM] Errore: Business Plan non valido",
                body=f"Il Manager-Bot ha riscontrato un errore nel leggere il file business_plan.yaml.\nErrore: {exc}\nControlla la sintassi YAML.",
                to_email=RECEIVER_EMAIL,
                sender_email=SENDER_EMAIL
            )
            return {}

def main():
    print("Manager-Bot avviato.")

    # Inizializza l'ambiente del Project-Bot e assicura che il modulo email_sender sia pronto
    send_email("TEST INIT", "Questo e' un test di inizializzazione.", RECEIVER_EMAIL, SENDER_EMAIL) 

    init_project_bot_env(OPENAI_API_KEY, RECEIVER_EMAIL, SENDER_EMAIL, GITHUB_TOKEN)

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