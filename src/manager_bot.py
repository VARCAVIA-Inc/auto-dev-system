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

    business_plan = read_business_plan()
    print(f"Contenuto parziale del Business Plan: {str(business_plan)[:200]}...")

    if business_plan and 'project_name' in business_plan and 'phases' in business_plan:
        print("Business Plan valido rilevato. Invocando il Project-Bot per i task...")
        
        # Iterare attraverso le fasi e i task
        for phase_index, phase in enumerate(business_plan['phases']):
            for task_index, task in enumerate(phase.get('tasks', [])):
                if task.get('agent') == 'ProjectBot' and task.get('status') == 'pending':
                    print(f"Trovato task pendente per ProjectBot: {task.get('description')}")
                    # Invoca ProjectBot passando i dettagli del task e gli indici
                    run_project_bot(task, task_index, phase_index) # <--- MODIFICATO
                    # Dopo che un task è stato gestito, esci per questa esecuzione.
                    # Il prossimo trigger del workflow (es. schedule) gestirà il prossimo task.
                    # Questo previene loop infiniti o eccessive chiamate API in un'unica esecuzione.
                    print("Un task gestito. Terminando questa esecuzione del Manager-Bot.")
                    return # Esci dalla funzione main dopo aver gestito un task

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