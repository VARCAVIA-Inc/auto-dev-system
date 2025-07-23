import os
import logging
import smtplib
import subprocess
import json
from email.mime.text import MIMEText
from src.utils.logging_utils import setup_logging
from src.utils.ai_utils import get_gemini_model, generate_response, PLANNING_MODEL

def get_system_status():
    """Raccoglie dati sullo stato dei workflow e delle Pull Request usando la CLI di GitHub."""
    logging.info("Raccolta dati sullo stato del sistema...")
    try:
        # Ottiene gli ultimi 5 run del workflow del ManagerBot
        runs_command = [
            'gh', 'run', 'list', 
            '--workflow', '1_manager_bot.yml', 
            '--limit', '5', 
            '--json', 'status,conclusion,displayTitle,url'
        ]
        runs_result = subprocess.run(runs_command, capture_output=True, text=True, check=True)
        runs_data = json.loads(runs_result.stdout)

        # Ottiene le Pull Request aperte create dai bot
        prs_command = [
            'gh', 'pr', 'list', 
            '--head', 'autodev/', 
            '--state', 'open', 
            '--json', 'title,url,createdAt'
        ]
        prs_result = subprocess.run(prs_command, capture_output=True, text=True) # Non usare check=True qui
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
        Sei l'AuditBot di VARCAVIA Office, un'IA responsabile della supervisione e della comunicazione.
        Analizza i seguenti dati grezzi in formato JSON, che rappresentano lo stato attuale dei workflow e delle Pull Request.

        Dati Grezzi:
        ---
        {context}
        ---

        Scrivi un'email chiara e professionale, come un rapporto per un dirigente. L'email deve includere:
        1.  **Oggetto:** Un titolo conciso (es. "VARCAVIA Office - Report Operativo").
        2.  **Panoramica:** Un riassunto dello stato generale del sistema (es. "Operativo", "In Stallo", "Errore Critico").
        3.  **Attività Recenti:** Descrivi l'esito degli ultimi workflow del ManagerBot.
        4.  **Lavoro in Corso:** Elenca le Pull Request attualmente aperte e create dal sistema. Se non ce ne sono, menzionalo.
        5.  **Prossimi Passaggi:** Sulla base dello stato attuale, indica qual è la prossima azione che il sistema intraprenderà (es. "Continuare l'esecuzione del piano di sviluppo", "Attendere nuove missioni").

        Usa un tono professionale, informativo e basato sui dati forniti.
        """
        
        report = generate_response(model, prompt)
        return report
    except Exception as e:
        logging.error(f"Impossibile generare il report: {e}")
        return "Errore durante la generazione del report di stato."

def send_email_report(report_content):
    # (Funzione invariata)
    # ...
    pass # Placeholder

def main():
    setup_logging()
    logging.info("--- AuditBot: Avviato. Inizio ciclo di supervisione e reporting. ---")
    
    status_data = get_system_status()
    if status_data:
        report_content = generate_status_report(status_data)
        if report_content:
            # La funzione send_email_report va completata come prima
            # send_email_report(report_content) 
            print("--- REPORT GENERATO ---")
            print(report_content)
            print("--- FINE REPORT ---")
            logging.info("Report generato. L'invio email è da implementare.")

    logging.info("--- AuditBot: Ciclo completato. ---")

if __name__ == "__main__":
    main()