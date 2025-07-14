import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
import os

def send_email(subject, body, to_email, sender_email=None):
    """
    Sends an email using SMTP.
    Requires EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD
    environment variables to be set.
    """
    smtp_host = os.getenv("EMAIL_HOST")
    smtp_port = int(os.getenv("EMAIL_PORT"))
    smtp_username = os.getenv("EMAIL_USERNAME")
    smtp_password = os.getenv("EMAIL_PASSWORD") # This is your App Password
    
    if not all([smtp_host, smtp_port, smtp_username, smtp_password]):
        print("Errore: Variabili d'ambiente per l'email non configurate correttamente.")
        print("Assicurati che EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD siano impostati.")
        return False

    if sender_email is None:
        sender_email = smtp_username # Use the SMTP username as sender if not specified

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = to_email

    # Add text part
    part_text = MIMEText(body, "plain")
    message.attach(part_text)

    try:
        # Create a secure SSL context
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, 465, context=context) as server: # Use 465 for SSL directly
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, to_email, message.as_string())
        print(f"Email inviata con successo a {to_email}")
        return True
    except Exception as e:
        print(f"Errore durante l'invio dell'email: {e}")
        # Try TLS on port 587 if SSL failed (some setups prefer STARTTLS)
        try:
            with smtplib.SMTP(smtp_host, 587) as server: # Use 587 for TLS
                server.starttls(context=context)
                server.login(smtp_username, smtp_password)
                server.sendmail(sender_email, to_email, message.as_string())
            print(f"Email inviata con successo a {to_email} (tentativo TLS).")
            return True
        except Exception as e_tls:
            print(f"Errore durante l'invio dell'email via TLS (587): {e_tls}")
            return False

# Esempio di utilizzo (solo per test, non verrà eseguito dal bot direttamente)
if __name__ == "__main__":
    # Questi valori sarebbero presi dalle variabili d'ambiente nel contesto reale
    # Per un test manuale, dovresti settarli qui o nel tuo ambiente locale
    # os.environ["EMAIL_HOST"] = "smtp.gmail.com"
    # os.environ["EMAIL_PORT"] = "587" # O 465 se usi SMTPS_SSL
    # os.environ["EMAIL_USERNAME"] = "workspace@varcavia.com"
    # os.environ["EMAIL_PASSWORD"] = "la_tua_app_password_di_16_caratteri"
    # os.environ["RECEIVER_EMAIL"] = "code@varcavia.com"
    # os.environ["SENDER_EMAIL"] = "workspace@varcavia.com"

    # send_email("Test dal Manager-Bot", "Questo è un messaggio di prova.", os.getenv("RECEIVER_EMAIL"))
    pass