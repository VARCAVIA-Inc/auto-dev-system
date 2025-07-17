import os
from src.utils.email_sender import send_email # Assicurati che l'import sia corretto

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
    # Leggiamo il nuovo riassunto dall'ambiente
    run_summary = os.getenv("RUN_SUMMARY", "Nessun dettaglio di esecuzione disponibile.")

    if not all([repo_name, run_id, job_status, workflow_name, receiver_email, sender_email]):
        return

    workflow_url = f"https://github.com/{repo_name}/actions/runs/{run_id}"

    # Usiamo il nuovo formato
    subject = f"VARCAVIA-Office Report: {workflow_name}"
    body = (
        f"Nuovo Run Effettuato\n\n"
        f"Report per: {workflow_name}\n"
        f"Dettagli: {run_summary}\n\n"
        f"Stato: {job_status.capitalize()}\n"
        f"Link al run:\n{workflow_url}"
    )
    
    print(f"Invio email di report a {receiver_email}...")
    # Assicurati che la funzione di invio email sia definita o importata correttamente
    send_email(subject, body, receiver_email, sender_email)
    print("Email di report inviata.")

if __name__ == "__main__":
    send_workflow_status_email()