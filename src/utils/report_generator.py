import os
from src.utils.email_sender import send_email

def send_workflow_status_email():
    """
    Analizza lo stato del workflow passato tramite variabili d'ambiente
    e invia una mail di riepilogo.
    """
    # Recupera le informazioni dall'ambiente di GitHub Actions
    repo_name = os.getenv("GITHUB_REPOSITORY")
    run_id = os.getenv("GITHUB_RUN_ID")
    job_status = os.getenv("JOB_STATUS")
    workflow_name = os.getenv("GITHUB_WORKFLOW")
    receiver_email = os.getenv("RECEIVER_EMAIL")
    sender_email = os.getenv("SENDER_EMAIL")

    if not all([repo_name, run_id, job_status, workflow_name, receiver_email, sender_email]):
        print("Errore: una o più variabili d'ambiente necessarie non sono state impostate.")
        return

    # Costruisci il link diretto alla pagina del run
    workflow_url = f"https://github.com/{repo_name}/actions/runs/{run_id}"

    # Prepara l'oggetto e il corpo della mail in base allo stato del job
    if job_status == "success":
        subject = f"✅ Successo: Workflow '{workflow_name}' completato"
        body = (
            f"Ciao,\n\n"
            f"Il workflow '{workflow_name}' nel repository {repo_name} è stato completato con successo.\n\n"
            f"Puoi visualizzare i dettagli del run qui:\n{workflow_url}\n\n"
            "Saluti,\nIl tuo AutoDevSystem."
        )
    else:
        subject = f"🚨 Fallimento: Workflow '{workflow_name}' ha riscontrato un errore"
        body = (
            f"Ciao,\n\n"
            f"Il workflow '{workflow_name}' nel repository {repo_name} è fallito.\n\n"
            f"Lo stato del job precedente è: **{job_status}**.\n\n"
            f"Per favore, controlla i log per identificare l'errore al seguente link:\n{workflow_url}\n\n"
            "Saluti,\nIl tuo AutoDevSystem."
        )
    
    print(f"Invio email di stato a {receiver_email}...")
    success = send_email(subject, body, receiver_email, sender_email)

    if success:
        print("Email di riepilogo inviata con successo.")
    else:
        print("Errore durante l'invio dell'email di riepilogo.")

if __name__ == "__main__":
    send_workflow_status_email()
