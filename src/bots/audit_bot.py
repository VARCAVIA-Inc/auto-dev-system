import os
import logging
import smtplib
from email.mime.text import MIMEText
from src.utils.logging_utils import setup_logging
from src.utils.ai_utils import get_gemini_model, generate_response, PLANNING_MODEL

def send_email_report(report_content):
    """Invia un report via email usando le credenziali dai segreti di GitHub."""
    logging.info("Preparazione del report via email...")
    host = os.getenv('EMAIL_HOST')
    port = os.getenv('EMAIL_PORT')
    user = os.getenv('EMAIL_USERNAME')
    password = os.getenv('EMAIL_PASSWORD')
    sender = os.getenv('SENDER_EMAIL')
    receiver = os.getenv('RECEIVER_EMAIL')

    if not all([host, port, user, password, sender, receiver]):
        logging.error("Una o più variabili d'ambiente per l'invio email non sono state trovate.")
        return

    subject = "VARCAVIA Office - Report di Stato Autonomo"
    msg = MIMEText(report_content, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver

    try:
        logging.info(f"Connessione al server SMTP {host}:{port}...")
        with smtplib.SMTP(host, int(port)) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(sender, [receiver], msg.as_string())
            logging.info(f"✅ Report inviato con successo a {receiver}.")
    except Exception as e:
        logging.error(f"❌ Fallimento nell'invio dell'email: {e}", exc_info=True)

def generate_status_report():
    """Usa Gemini per generare un report di stato esplicativo."""
    logging.info("Richiesta a Gemini di generare il report di stato...")
    try:
        model = get_gemini_model(PLANNING_MODEL)
        
        # TODO: In futuro, raccogliere qui il contesto reale (log, PR, commit)
        context = "Il sistema è operativo. L'ultimo ciclo del ManagerBot si è concluso con successo. Non ci sono task attivi. La prossima missione è implementare le notifiche email."

        prompt = f"""
        Sei l'AuditBot di VARCAVIA Office, un'intelligenza artificiale responsabile della supervisione e della comunicazione.
        Scrivi un'email chiara e professionale, come un rapporto per un dirigente, che riassuma lo stato attuale del sistema.

        Contesto attuale:
        ---
        {context}
        ---

        L'email deve includere:
        1.  **Oggetto:** Un titolo chiaro e conciso.
        2.  **Panoramica:** Un breve riassunto dello stato generale del sistema (operativo, in errore, etc.).
        3.  **Attività Recenti:** Spiega cosa è stato fatto nell'ultimo ciclo.
        4.  **Valutazione del Piano:** Valuta brevemente lo stato del piano di sviluppo.
        5.  **Prossimi Passaggi:** Dichiara qual è la prossima missione in programma.

        Usa un tono professionale e informativo.
        """
        
        report = generate_response(model, prompt)
        return report
    except Exception as e:
        logging.error(f"Impossibile generare il report: {e}")
        return "Errore durante la generazione del report di stato."


def main():
    setup_logging()
    logging.info("--- AuditBot: Avviato. Inizio ciclo di supervisione e reporting. ---")
    
    report_content = generate_status_report()
    
    if report_content:
        send_email_report(report_content)
    
    logging.info("--- AuditBot: Ciclo completato. ---")

if __name__ == "__main__":
    main()