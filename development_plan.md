# Piano di Sviluppo

## Obiettivo
Implementare un sistema di autenticazione utenti base con funzionalità di login e registrazione.

## Tecnologie Utilizzate
- Linguaggio di programmazione: Python
- Framework web: Flask
- Database: SQLite

## Architettura del Progetto
- `/app`
  - `/templates`
    - `register.html`
    - `login.html`
  - `/static`
    - `styles.css` (per futuro utilizzo)
  - `app.py`
  - `models.py`
  - `auth.py`
  - `test_auth.py`
  - `database.db`
  
## Checklist di Sviluppo

### 1. Impostazione dell'ambiente di sviluppo
- [ ] Creare una cartella chiamata `app`.
- [ ] Inizializzare un ambiente virtuale Python all'interno della cartella del progetto.
- [ ] Installare Flask utilizzando `pip install flask`.
- [ ] Creare un file `app.py` per l'inizializzazione dell'applicazione Flask.

### 2. Configurazione di base dell'applicazione
- [ ] Configurare l'app Flask in `app.py` con le seguenti specifiche:
  - [ ] Importare la classe Flask.
  - [ ] Creare l'istanza dell'app Flask.
  - [ ] Configurare le chiavi segrete e le opzioni del database.

### 3. Creazione del database
- [ ] Installare SQLite (se non disponibile).
- [ ] Creare un file `models.py` per definire i modelli di dati:
  - [ ] Definire un modello `User` con gli attributi `id`, `username`, `password_hash`.
- [ ] Creare e inizializzare il database:
  - [ ] Scrivere uno script per creare il database `database.db` e la tabella `users`.

### 4. Implementazione del sistema di registrazione
- [ ] Creare un file `auth.py` per gestire l'autenticazione:
  - [ ] Definire la funzione `register(user_data)` per la registrazione degli utenti:
    - [ ] Verificare se l'utente esiste già.
    - [ ] Inserire il nuovo utente nella tabella `users`.
    - [ ] Ritornare un messaggio di conferma o errore.
- [ ] Creare un template `register.html`:
  - [ ] Aggiungere un modulo con campi `username` e `password`.

### 5. Implementazione del sistema di login
- [ ] In `auth.py`, definire la funzione `login(user_data)`:
  - [ ] Verificare le credenziali dell'utente.
  - [ ] Se valide, creare una sessione utente.
  - [ ] Ritornare un messaggio di conferma o errore.
- [ ] Creare un template `login.html`:
  - [ ] Aggiungere un modulo con campi `username` e `password`.

### 6. Integrazione delle funzionalità di autenticazione
- [ ] Modificare `app.py` per includere le rotte di registrazione e login.
- [ ] Aggiungere meccanismi di sessione per la gestione dello stato dell'utente.

### 7. Scrittura dei test
- [ ] Creare un file `test_auth.py` per definire i test automatizzati:
  - [ ] Scrivere test per la registrazione:
    - [ ] Verificare la registrazione con dati validi.
    - [ ] Verificare gestione di utenti duplicati.
  - [ ] Scrivere test per il login:
    - [ ] Verificare l'accesso con credenziali corrette.
    - [ ] Verificare gestione di credenziali errate.

### 8. Validazione e Verifica
- [ ] Testare manualmente l'applicazione per garantire il corretto funzionamento.
- [ ] Verificare la gestione corretta delle sessioni e la sicurezza delle password (crittografia hashing).

### 9. Manutenzione e Documentazione
- [ ] Documentare il codice e le funzionalità del sistema.
- [ ] Preparare un file `README.md` con le istruzioni per l'installazione e l'uso.

### Conclusione
Il progetto deve essere utilizzabile per un sistema di autenticazione di base in una applicazione web personale o educativa. La sicurezza e altre funzionalità avanzate, come la gestione delle password smarrite, saranno considerate come lavori futuri.