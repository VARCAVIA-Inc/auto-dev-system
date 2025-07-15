import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl

def send_email(subject, body, to_email, sender_email=None):
    smtp_host = os.getenv("EMAIL_HOST")
    smtp_port = int(os.getenv("EMAIL_PORT", 587))
    smtp_username = os.getenv("EMAIL_USERNAME")
    smtp_password = os.getenv("EMAIL_PASSWORD")
    
    if not all([smtp_host, smtp_port, smtp_username, smtp_password]):
        print("Errore: Variabili d'ambiente per l'email non configurate.")
        return False

    if sender_email is None:
        sender_email = smtp_username

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = to_email
    message.attach(MIMEText(body, "plain"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls(context=context)
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, to_email, message.as_string())
        return True
    except Exception as e:
        print(f"Errore durante l'invio dell'email: {e}")
        return False

def send_workflow_status_email():
    repo_name = os.getenv("GITHUB_REPOSITORY")
    run_id = os.getenv("GITHUB_RUN_ID")
    job_status = os.getenv("JOB_STATUS")
    workflow_name = os.getenv("GITHUB_WORKFLOW")
    receiver_email = os.getenv("RECEIVER_EMAIL")
    sender_email = os.getenv("SENDER_EMAIL")

    if not all([repo_name, run_id, job_status, workflow_name, receiver_email, sender_email]):
        print("Errore: una o più variabili d'ambiente per il report non sono state impostate.")
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