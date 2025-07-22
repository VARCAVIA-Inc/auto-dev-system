Ricevuto. Sto analizzando l'obiettivo di business e la struttura del progetto.

Ecco il piano tecnico dettagliato per gli OperatorBot.

---

**TO:** OperatorBots
**FROM:** ProjectBot (CTO)
**DATE:** 2023-10-27
**SUBJECT:** Piano Tecnico - Potenziamento Email per AuditBot

## Obiettivo

Potenziare `AuditBot` per generare e inviare un report di riepilogo via email sullo stato dell'ultimo ciclo di `ManagerBot`. L'implementazione utilizzerà le utility e le credenziali `EMAIL_*` esistenti.

## Piano di Esecuzione

Seguire i seguenti passaggi in ordine sequenziale.

### Fase 1: Setup e Preparazione dell'Ambiente

1.  - [ ] [shell-command] `git checkout main`
2.  - [ ] [shell-command] `git pull origin main`
3.  - [ ] [shell-command] `git checkout -b feature/auditbot-email-reporting`
4.  - [ ] [shell-command] `mkdir -p run`
5.  - [ ] [shell-command] `echo "*" > run/.gitignore`
6.  - [ ] [shell-command] `git add run/.gitignore && git commit -m "chore: create and ignore run directory for ephemeral data"`

### Fase 2: Modifica di ManagerBot per Salvare lo Stato

`ManagerBot` deve salvare il suo stato finale in un file strutturato e prevedibile, in modo che `AuditBot` possa leggerlo. Useremo un file JSON nella directory `run/`.

1.  - [ ] **[src/bots/manager_bot.py]** Modificare il file `manager_bot.py` per salvare lo stato.
    - Aggiungere gli import necessari all'inizio del file: `import json` e `import os`.
    - Alla fine del suo ciclo di esecuzione principale, aggiungere la logica per creare un dizionario di riepilogo (es. `status_summary = {"status": "COMPLETED", "tasks_run": 5, "errors": 0}`).
    - Assicurarsi che la directory `run/` esista: `os.makedirs('run', exist_ok=True)`.
    - Scrivere il dizionario in un file JSON: `with open('run/manager_status.json', 'w') as f: json.dump(status_summary, f, indent=4)`.

### Fase 3: Potenziamento di AuditBot per l'Invio di Email

Questo è il cuore della modifica. `AuditBot` leggerà il file di stato, comporrà l'email e la invierà.

1.  - [ ] **[src/bots/audit_bot.py]** Modificare il file `audit_bot.py`.
    - Aggiungere gli import necessari: `import json`, `import os` e `from utils.email_sender import send_email`.
    - Nel metodo principale di `AuditBot`, implementare la seguente logica:
        - Definire il percorso del file di stato: `status_file_path = 'run/manager_status.json'`.
        - Controllare se il file esiste. Se non esiste, registrare un avviso (log a warning) e terminare la funzione di reporting.
        - Se il file esiste, leggerlo e caricare i dati JSON.
        - Recuperare l'indirizzo email del destinatario da una variabile d'ambiente. Questo disaccoppia la configurazione dal codice: `recipient_email = os.getenv('AUDIT_RECIPIENT_EMAIL')`. Aggiungere un controllo per assicurarsi che la variabile sia impostata.
        - Formattare il corpo e l'oggetto dell'email. Esempio:
            - `subject = "Riepilogo Ciclo ManagerBot"`
            - `body = f"Report di stato per l'ultimo ciclo di ManagerBot:\n\n{json.dumps(status_data, indent=2)}"`
        - Invocare la funzione di invio email: `send_email(recipient=recipient_email, subject=subject, body=body)`.
        - Gestire eventuali eccezioni durante l'invio dell'email e registrarle (log an error).
        - Dopo l'elaborazione, eliminare il file di stato per evitare di inviare nuovamente lo stesso report: `os.remove(status_file_path)`.

### Fase 4: Configurazione e Test

Dobbiamo assicurarci che la configurazione sia documentata e che il nuovo flusso di lavoro possa essere testato.

1.  - [ ] **[README.md]** Aggiornare il file `README.md` principale.
    - Aggiungere una nuova sezione intitolata `Configurazione Email di Audit`.
    - Documentare la nuova variabile d'ambiente richiesta: `AUDIT_RECIPIENT_EMAIL`. Spiegare che questo è l'indirizzo a cui verranno inviati i report di riepilogo.

2.  - [ ] **[scripts/test_audit_email.py]** Creare uno script di test per verificare la funzionalità in isolamento.
    - Lo script deve:
        1. Importare `os`, `json`, `sys` e aggiungere `src` al path.
        2. Importare la funzione `send_email` da `utils.email_sender`.
        3. Creare un file `run/manager_status.json` fittizio per il test. Esempio: `{'status': 'TEST_SUCCESS', 'message': 'This is a test report.'}`.
        4. Impostare la variabile d'ambiente `AUDIT_RECIPIENT_EMAIL`.
        5. Invocare la logica di reporting di `AuditBot` (potrebbe essere necessario refattorizzare la logica in una funzione richiamabile all'interno di `audit_bot.py`).
        6. Stampare un messaggio di successo o fallimento.

3.  - [ ] **[shell-command]** Eseguire il test (assicurarsi che le variabili d'ambiente `EMAIL_*` e `AUDIT_RECIPIENT_EMAIL` siano impostate nella shell corrente).
    ```bash
    export AUDIT_RECIPIENT_EMAIL="your-test-email@example.com"
    python scripts/test_audit_email.py
    ```

### Fase 5: Finalizzazione

1.  - [ ] **[shell-command]** Rimuovere i file di test temporanei se lo script di test non viene committato. Se lo script viene committato, modificare il `.gitignore` per ignorare i file di stato generati localmente. (Nota: Il `run/.gitignore` della Fase 1 dovrebbe già gestire questo).
2.  - [ ] **[shell-command]** Formattare il codice per garantire la coerenza.
    ```bash
    # (assumendo l'uso di 'black' o un altro linter/formatter)
    # black .
    ```
3.  - [ ] [shell-command] `git add .`
4.  - [ ] [shell-command] `git commit -m "feat(auditbot): implement email reporting for managerbot status"`
5.  - [ ] [shell-command] `git push origin feature/auditbot-email-reporting`
6.  - [ ] Creare una Pull Request su GitHub dal branch `feature/auditbot-email-reporting` a `main`. Assegnare a ProjectBot per la revisione.

Eseguire.