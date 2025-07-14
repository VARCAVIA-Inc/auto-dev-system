import os
import openai
from src.utils.email_sender import send_email

# Inizializza il client OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

def generate_response_with_ai(prompt):
    """
    Genera una risposta usando l'API di OpenAI.
    """
    try:
        completion = openai.chat.completions.create(
            model="gpt-4o-mini", # O un altro modello che preferisci, es. "gpt-4o"
            messages=[
                {"role": "system", "content": "Sei un assistente AI utile."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except openai.APIError as e:
        print(f"Errore API OpenAI: {e}")
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore API OpenAI",
            body=f"Il Project-Bot ha riscontrato un errore con l'API di OpenAI.\nErrore: {e}",
            to_email=RECEIVER_EMAIL,
            sender_email=SENDER_EMAIL
        )
        return None
    except Exception as e:
        print(f"Errore generico durante la chiamata OpenAI: {e}")
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore Project-Bot (OpenAI)",
            body=f"Il Project-Bot ha riscontrato un errore generico durante la chiamata OpenAI.\nErrore: {e}",
            to_email=RECEIVER_EMAIL,
            sender_email=SENDER_EMAIL
        )
        return None

def run_project_bot(task_description):
    """
    Funzione principale del Project-Bot.
    Prende una descrizione del task e la elabora.
    """
    print(f"Project-Bot avviato per il task: {task_description}")

    # Esempio di utilizzo dell'AI: chiedere una breve descrizione
    ai_prompt = f"Genera una breve descrizione per il seguente task di sviluppo: '{task_description}'."
    ai_response = generate_response_with_ai(ai_prompt)

    if ai_response:
        print(f"Risposta AI per il task: {ai_response}")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Completato: {task_description[:50]}...",
            body=f"Il Project-Bot ha elaborato il task:\n'{task_description}'\n\nRisposta AI:\n{ai_response}",
            to_email=RECEIVER_EMAIL,
            sender_email=SENDER_EMAIL
        )
    else:
        print("Il Project-Bot non è riuscito a generare una risposta AI.")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Fallito: {task_description[:50]}...",
            body=f"Il Project-Bot non è riuscito a generare una risposta AI per il task:\n'{task_description}'",
            to_email=RECEIVER_EMAIL,
            sender_email=SENDER_EMAIL
        )

    print("Project-Bot completato.")

if __name__ == "__main__":
    # Questo blocco non verrà eseguito in un workflow reale,
    # ma è utile per testare il bot individualmente.
    print("Esecuzione diretta del Project-Bot (solo per test).")
    run_project_bot("Crea una funzione Python per calcolare il fattoriale di un numero.")