import os
import yaml
from github import Github
from src.utils.email_sender import send_email
from src.project_bot import run_project_bot # <--- AGGIUNGI QUESTA RIGA

# --- Inizializzazione ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

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

# --- Funzioni del Manager-Bot ---

def send_initial_status_email():
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
    business_plan_path = 'src/business_plan.yaml'
    if not os.path.exists(business_plan_path):
        print(f"Avviso: Il Business Plan non trovato in {business_plan_path}. Creazione di un file vuoto.")
        # Il contenuto di esempio verrà aggiunto nel prossimo passo, qui lo lasciamo vuoto per non sovrascrivere
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
    # send_initial_status_email() # Non inviamo più questa email ad ogni avvio, la useremo per notifiche specifiche

    business_plan = read_business_plan()
    print(f"Contenuto parziale del Business Plan: {str(business_plan)[:200]}...")

    if business_plan and 'project_name' in business_plan and 'phases' in business_plan:
        print("Business Plan valido rilevato. Invocando il Project-Bot per i task...")
        # Per ora, prendiamo il primo task del primo phase per test
        if business_plan['phases'] and business_plan['phases'][0]['tasks']:
            first_task = business_plan['phases'][0]['tasks'][0]['description']
            print(f"Invocando Project-Bot con il task: {first_task}")
            run_project_bot(first_task)
        else:
            print("Nessun task trovato nel Business Plan. In attesa di istruzioni.")
            send_email(
                subject="[AUTO-DEV-SYSTEM] Manager-Bot in attesa",
                body="Il Manager-Bot ha letto il Business Plan ma non ha trovato task da eseguire. In attesa di istruzioni.",
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