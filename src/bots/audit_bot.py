import os
import logging
import smtplib
import subprocess
import json
from email.mime.text import MIMEText
from src.utils.logging_utils import setup_logging
from src.utils.ai_utils import get_gemini_model, generate_response, PLANNING_MODEL

def get_system_status():
    """Raccoglie dati sullo stato dei workflow e delle Pull Request."""
    logging.info("Raccolta dati sullo stato del sistema...")
    try:
        runs_command = ['gh', 'run', 'list', '--workflow', '1_manager_bot.yml', '--limit', '5', '--json', 'status,conclusion,displayTitle,url']
        runs_result = subprocess.run(runs_command, capture_output=True, text=True, check=True)
        runs_data = json.loads(runs_result.stdout)
        prs_command = ['gh', 'pr', 'list', '--head', 'autodev/', '--state', 'open', '--json', 'title,url,createdAt']
        prs_result = subprocess.run(prs_command, capture_output=True, text=True)
        prs_data = json.loads(prs_result.stdout) if prs_result.stdout else []
        return {"runs": runs_data, "prs": prs_data}
    except Exception as e:
        logging.error(f"Errore durante la raccolta dati: {e}", exc_info=True)
        return None

def generate_status_report(status_data):
    """Usa Gemini per analizzare i dati e generare un report di stato."""
    logging.info("Richiesta a Gemini di generare il report di stato analitico...")
    try:
        model = get_gemini_model(PLANNING_MODEL)
        context = json.dumps(status_data, indent=2)
        prompt = f"""
        Sei l'AuditBot di VARCAVIA Office, un'IA responsabile della supervisione.
        Analizza i seguenti dati JSON sullo stato dei workflow e delle Pull Request.

        Dati:
        ---
        {context}
        ---

        Scrivi un'email chiara e professionale per un dirigente. L'email deve includere:
        1.  **Oggetto:** "VARCAVIA Office - Report Operativo".
        2.  **Panoramica:** Un riassunto dello stato generale del sistema.
        3.  **Attività Recenti:** Descrivi l'esito degli ultimi workflow.
        4.  **Lavoro in Corso:** Elenca le Pull Request aperte.
        5.  **Prossimi Passaggi:** Indica la prossima azione che il sistema intraprenderà.
        """
        report = generate_response(model, prompt)
        return report
    except Exception as e:
        logging.error(f"Impossibile generare il report: {e}")
        return "Errore durante la generazione del report di stato."

def send_email_report(report_content):
    host, port, user, password, sender, receiver = (os.getenv(k) for k in ['EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_USERNAME', 'EMAIL_PASSWORD', 'SENDER_EMAIL', 'RECEIVER_EMAIL'])
    if not all([host, port, user, password, sender, receiver]):
        logging.error("Mancano le variabili d'ambiente per l'invio email.")
        return
    try:
        msg = MIMEText(report_content, 'plain', 'utf-8')
        msg['Subject'] = "VARCAVIA Office - Report Operativo Autonomo"
        msg['From'] = sender
        msg['To'] = receiver
        logging.info(f"Connessione al server SMTP {host}:{port}...")
        with smtplib.SMTP(host, int(port)) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(sender, [receiver], msg.as_string())
            logging.info(f"✅ Report inviato con successo a {receiver}.")
    except Exception as e:
        logging.error(f"❌ Fallimento nell'invio dell'email: {e}", exc_info=True)

def main():
    setup_logging()
    logging.info("--- AuditBot: Avviato. Inizio ciclo di supervisione e reporting. ---")
    status_data = get_system_status()
    if status_data:
        report_content = generate_status_report(status_data)
        if report_content:
            send_email_report(report_content)
    logging.info("--- AuditBot: Ciclo completato. ---")

if __name__ == "__main__":
    main()