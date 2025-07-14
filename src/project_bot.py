# Funzioni principali del Project-Bot
def generate_response_with_ai(prompt, openai_api_key, receiver_email, sender_email, model="gpt-4o-mini"): # <--- NUOVI ARGOMENTI
    """
    Genera una risposta usando l'API di OpenAI.
    """
    if not openai_api_key:
        print("Errore: OPENAI_API_KEY non configurata per la chiamata AI. Impossibile generare contenuto.")
        return None
    
    # Imposta la chiave API di OpenAI QUI, per questa singola chiamata
    openai.api_key = openai_api_key 
    
    print(f"DEBUG: Tentativo di chiamata OpenAI API. Prompt: {prompt[:100]}...")
    
    try:
        completion = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Sei un assistente AI utile e specializzato nella generazione di codice e contenuti tecnici."},
                {"role": "user", "content": prompt}
            ]
        )
        print("Risposta OpenAI ricevuta.")
        return completion.choices[0].message.content
    except openai.AuthenticationError as e:
        print(f"Errore di autenticazione OpenAI: {e}. Controlla la OPENAI_API_KEY.")
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore di Autenticazione OpenAI",
            body=f"Il Project-Bot ha riscontrato un errore di autenticazione con l'API di OpenAI.\nErrore: {e}\nAssicurati che OPENAI_API_KEY sia corretta e valida.",
            to_email=receiver_email, # Usa gli argomenti per l'email
            sender_email=sender_email
        )
        return None
    except openai.APICallError as e:
        print(f"Errore durante la chiamata API OpenAI: {e}. Code: {e.code}, Type: {e.type}")
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore API OpenAI",
            body=f"Il Project-Bot ha riscontrato un errore durante la chiamata API di OpenAI.\nErrore: {e}\nCode: {e.code}, Type: {e.type}",
            to_email=receiver_email, # Usa gli argomenti per l'email
            sender_email=sender_email
        )
        return None
    except Exception as e:
        print(f"Errore generico durante la chiamata OpenAI: {e}. Tipo: {type(e)}")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Errore Project-Bot (OpenAI Generico)",
            body=f"Il Project-Bot ha riscontrato un errore generico durante la chiamata OpenAI.\nErrore: {e}\nTipo: {type(e)}",
            to_email=receiver_email, # Usa gli argomenti per l'email
            sender_email=sender_email
        )
        return None

def create_file_task(task_details, openai_api_key, receiver_email, sender_email): # <--- NUOVI ARGOMENTI
    """
    Gestisce il task di creazione di un file.
    """
    print("Inizio funzione create_file_task.")
    file_path = task_details.get('path')
    prompt_for_content = task_details.get('prompt_for_content')

    print(f"Dettagli task creazione file: path='{file_path}', prompt_for_content='{prompt_for_content[:50]}...'")

    if not file_path:
        print("Errore: 'path' non specificato per il task 'create_file'. Restituisco False.")
        return False

    print(f"Tentativo di creazione file: {file_path}")
    content = ""
    if prompt_for_content:
        print(f"Generando contenuto AI per il file: {file_path}...")
        try:
            ai_generated_content = generate_response_with_ai(prompt_for_content, openai_api_key, receiver_email, sender_email) # <--- PASSA ARGOMENTI
        except Exception as e:
            print(f"Errore inaspettato durante la chiamata generate_response_with_ai: {e}")
            ai_generated_content = None
        
        if ai_generated_content:
            content = ai_generated_content
        else:
            print("Impossibile generare contenuto AI. Il file non verrà creato. Restituisco False.")
            return False

    try:
        dir_name = os.path.dirname(file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        
        full_path = os.path.join(get_repo_root(), file_path)
        print(f"Scrivendo il file completo in: {full_path}")
        with open(full_path, 'w') as f:
            f.write(content)
        print(f"File '{full_path}' creato/aggiornato con successo.")
        return True
    except Exception as e:
        print(f"Errore durante la creazione del file '{file_path}': {e}. Restituisco False.")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Errore Project-Bot: Creazione file fallita",
            body=f"Il Project-Bot non è riuscito a creare il file '{file_path}'.\nErrore: {e}",
            to_email=receiver_email, # Usa gli argomenti per l'email
            sender_email=sender_email
        )
        return False

def update_business_plan_status(task_index, phase_index, new_status="completed"):
    global _receiver_email, _sender_email # Mantenuto qui perché send_email è chiamato
    repo_root = get_repo_root()
    business_plan_path = os.path.join(repo_root, 'src', 'business_plan.yaml')

    print(f"Tentativo di aggiornare BP per task {task_index} fase {phase_index} a {new_status}")

    try:
        with open(business_plan_path, 'r') as file:
            plan = yaml.safe_load(file)

        if plan and 'phases' in plan and len(plan['phases']) > phase_index and \
           'tasks' in plan['phases'][phase_index] and \
           len(plan['phases'][phase_index]['tasks']) > task_index:
            
            plan['phases'][phase_index]['tasks'][task_index]['status'] = new_status
            
            with open(business_plan_path, 'w') as file:
                yaml.dump(plan, file, default_flow_style=False, sort_keys=False)

            print(f"Stato del task {task_index} nella fase {phase_index} aggiornato a '{new_status}'.")
            return True
        else:
            print("Avviso: Impossibile trovare il task da aggiornare nel Business Plan.")
            return False

    except Exception as e:
        print(f"Errore durante l'aggiornamento del Business Plan (solo scrittura file): {e}")
        send_email(
            subject="[AUTO-DEV-SYSTEM] Errore Project-Bot: Aggiornamento Business Plan (solo scrittura) fallito",
            body=f"Il Project-Bot non è riuscito a scrivere il business_plan.yaml dopo l'aggiornamento dello stato.\nErrore: {e}",
            to_email=_receiver_email, # Usa la variabile globale per l'email qui
            sender_email=_sender_email
        )
        return False

def run_project_bot(task_details, task_index, phase_index):
    """
    Funzione principale del Project-Bot.
    Prende i dettagli del task e li elabora.
    """
    global _receiver_email, _sender_email, _openai_api_key # Aggiungi _openai_api_key qui
    task_description = task_details.get('description', 'N/A')
    task_type = task_details.get('type')
    
    print(f"Inizio esecuzione run_project_bot per task: '{task_description}' (Tipo: {task_type}).")
    print(f"Task details completi: {task_details}")
    
    task_completed = False
    commit_message = f"feat: {task_description[:70]}..."

    # 1. Esegui l'azione del task
    if task_type == 'create_file':
        print("Rilevato task_type 'create_file'. Chiamata create_file_task.")
        task_completed = create_file_task(task_details, _openai_api_key, _receiver_email, _sender_email) # <--- PASSA ARGOMENTI
        if task_completed:
            print("create_file_task completato con successo.")
        else:
            print("create_file_task ha restituito False (fallimento).")
        commit_message = f"feat: Create file {task_details.get('path', 'unknown')}"
    elif task_type == 'info' or task_type == 'action' or task_type == 'generate_code':
        print(f"Rilevato task_type '{task_type}'. Processando via AI prompt.")
        ai_prompt = f"Genera un messaggio per il completamento del seguente task: '{task_description}'."
        ai_response = generate_response_with_ai(ai_prompt, _openai_api_key, _receiver_email, _sender_email) # <--- PASSA ARGOMENTI
        if ai_response:
            print(f"Risposta AI per il task '{task_description}': {ai_response}")
            task_completed = True
        else:
            print("Il Project-Bot non è riuscito a generare una risposta AI per il task info/action.")
            task_completed = False
        commit_message = f"chore: Processed info/action task: {task_description[:50]}"
    else:
        print(f"Tipo di task sconosciuto: {task_type}. Nessuna azione specifica.")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Sconosciuto: {task_description[:50]}...",
            body=f"Il Project-Bot ha incontrato un task con tipo sconosciuto: '{task_type}' per la descrizione: '{task_description}'.",
            to_email=_receiver_email,
            sender_email=_sender_email
        )
        task_completed = False

    # 2. Aggiorna lo stato del Business Plan (localmente)
    bp_update_successful = update_business_plan_status(task_index, phase_index, "completed" if task_completed else "failed")
    if not bp_update_successful:
        print("Errore: Fallimento nella scrittura locale dello stato del Business Plan.")
        task_completed = False # Considera il task fallito se non si può aggiornare il BP

    # 3. Committa e pusha le modifiche sul nuovo branch e crea PR (se ci sono modifiche)
    if task_completed and bp_update_successful:
        print("Tentativo di commit e push su nuovo branch e creazione PR.")
        push_and_pr_successful = commit_and_push_on_new_branch(get_repo_root(), commit_message)
        
        # 4. Notifica finale via email
        if push_and_pr_successful:
            send_email(
                subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Completato e PR Creata: {task_description[:50]}...",
                body=f"Il Project-Bot ha completato con successo il task:\n'{task_description}'\n\nÈ stata creata una Pull Request per unire le modifiche. Controlla il tuo repository GitHub.",
                to_email=_receiver_email,
                sender_email=_sender_email
            )
        else:
            print("Avviso: Task completato localmente, ma push o PR falliti.")
            send_email(
                subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Completato (Richiede Intervento Manuale): {task_description[:50]}...",
                body=f"Il Project-Bot ha completato il task:\n'{task_description}'\n\n**ATTENZIONE:** Il push delle modifiche o la creazione della Pull Request sono falliti. Controllare i log di GitHub Actions per i dettagli. Potrebbe essere necessario un intervento manuale per recuperare le modifiche e unirle.",
                to_email=_receiver_email,
                sender_email=_sender_email
            )
    else:
        print("Task fallito o BP non aggiornato. Nessun push o PR effettuata.")
        send_email(
            subject=f"[AUTO-DEV-SYSTEM] Project-Bot - Task Fallito: {task_description[:50]}...",
            body=f"Il Project-Bot non è riuscito a completare il task:\n'{task_description}'.\n\nControlla i log di GitHub Actions per i dettagli.",
            to_email=_receiver_email,
            sender_email=_sender_email
        )

    print("Fine esecuzione run_project_bot.")

if __name__ == "__main__":
    pass