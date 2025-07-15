import os
from src.utils.email_sender import send_email

def send_workflow_status_email():
    """
    Analizza lo stato del workflow e invia una mail di riepilogo.
    """
    repo_name = os.getenv("GITHUB_REPOSITORY")
    run_id = os.getenv("GITHUB_RUN_ID")
    job_status = os.getenv("JOB_STATUS")
    workflow_name = os.getenv("GITHUB_WORKFLOW")
    receiver_email = os.getenv("RECEIVER_EMAIL")
    sender_email = os.getenv("SENDER_EMAIL")

    if not all([repo_name, run_id, job_status, workflow_name, receiver_email, sender_email]):
        print("Errore: una o più variabili d'ambiente necessarie per il report non sono state impostate.")
        return

    workflow_url = f"[https://github.com/](https://github.com/){repo_name}/actions/runs/{run_id}"

    if job_status == "success":
        subject = f"✅ Report Successo: {workflow_name}"
        body = (
            f"Report per: {workflow_name}\n\n"
            f"Stato: Eseguito con successo.\n\n"
            f"Dettagli del run:\n{workflow_url}"
        )
    else:
        subject = f"🚨 Report Fallimento: {workflow_name}"
        body = (
            f"Report per: {workflow_name}\n\n"
            f"Stato: Fallito (risultato del job: {job_status}).\n\n"
            f"Controlla i log per i dettagli:\n{workflow_url}"
        )
    
    print(f"Invio email di report a {receiver_email}...")
    send_email(subject, body, receiver_email, sender_email)
    print("Email di report inviata.")

if __name__ == "__main__":
    send_workflow_status_email()