import os
import yaml # Per leggere il Business Plan
from github import Github # Per interagire con GitHub API
from src.utils.email_sender import send_email # Il nostro modulo per l'email

# --- Inizializzazione ---
# Recupera le variabili d'ambiente (i Secret di GitHub)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

# Inizializza il client GitHub
try:
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(os.getenv("GITHUB_REPOSITORY")) # Recupera il repo corrente
    print(f"Connesso al repository: {repo.full_name}")
except Exception as e:
    print(f"Errore durante l'inizializzazione di GitHub API: {e}")
    # Invia un'email di errore se la connessione GitHub fallisce
    send_email(
        subject="[AUTO-DEV-SYSTEM] Errore critico: GitHub API non inizializzata",
        body=f"Il Manager-Bot non è riuscito a connettersi all'API di GitHub.\nErrore: {e}\nAssicurati che BOT_GITHUB_TOKEN sia corretto e con i permessi necessari.",
        to_email=RECEIVER_EMAIL,
        sender_email=SENDER_EMAIL
    )
    exit(1) # Termina lo script se non si connette a GitHub

# --- Funzioni del Manager-Bot ---

def send_initial_status_email():
    """
    Invia un'email per confermare l'avvio del Manager-Bot.
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
            f.write("# Verrà letto e interpretato dai bot per generare il codice.\n")
            f.write("# Esempio:\n")
            f.write("# project_name: MyAwesomeApp\n")
            f.write("# phases:\n")
            f.write("#   - name: Setup\n")
            f.write("#     tasks:\n")
            f.write("#       - description: Initialize project structure\n")
            f.write("#         agent: ProjectBot\n")
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
    send_initial_status_email()
    business_plan = read_business_plan()
    print(f"Contenuto parziale del Business Plan: {str(business_plan)[:200]}...") # Mostra un estratto

    # --- Qui verrà la logica più complessa ---
    # Per ora, solo un placeholder.
    # Il ProjectBot verrà invocato da qui in futuro per iniziare lo sviluppo.
    # Es: if 'project_name' in business_plan:
    #         # Invocare ProjectBot
    # else:
    #         send_email("Manager-Bot in attesa", "Nessun Business Plan valido trovato. In attesa di istruzioni.", RECEIVER_EMAIL, SENDER_EMAIL)

    print("Manager-Bot completato per questa esecuzione.")

if __name__ == "__main__":
    main()