# Piano di Sviluppo

## Obiettivo
Implementare un sistema di autenticazione utenti base con funzionalità di login e registrazione.

---

## Checklist dei Sotto-Task

### 1. Configurazione dell'Ambiente
- [ ] **Impostare il progetto con struttura MVC:**
  - Creare directory `models`, `views`, `controllers`, `routes`.
  - Creare un file di configurazione `config.js`.

### 2. Creazione del Database
- [ ] **Impostare il database per memorizzare gli utenti:**
  - Creare uno schema di database con una tabella `users` (campi: `id`, `username`, `email`, `passwordHash`).
  - File: `database/schema.sql`

### 3. Configurazione delle Dipendenze
- [ ] **Installare le dipendenze necessarie:**
  - Installare `express` per la gestione delle richieste HTTP.
  - Installare `bcrypt` per l'hashing delle password.
  - Installare `jsonwebtoken` per la sicurezza del token.
  - Installare `sequelize` per l'interfacciamento con il database.

### 4. Implementazione del Modello Utente
- [ ] **Definire il modello per gli utenti:**
  - Creare `models/User.js`.
  - Implementare il modello degli utenti utilizzando `sequelize`.
  - Aggiungere metodi per:
    - Registrare un nuovo utente.
    - Verificare le credenziali utente.

### 5. Creazione del Controller di Autenticazione
- [ ] **Implementare il controller per gestire l'autenticazione:**
  - Creare `controllers/authController.js`.
  - Definire le seguenti funzioni:
    - `register(req, res)`: Registra un nuovo utente.
    - `login(req, res)`: Autentica un utente e fornisce un JWT.
    - `hashPassword(password)`: Hasha la password utilizzando bcrypt.
    - `validateUserData(email, password)`: Valida i dati in ingresso.

### 6. Configurazione delle Rotte
- [ ] **Definire le rotte per la registrazione e il login:**
  - Creare `routes/authRoutes.js`.
  - Aggiungere le seguenti rotte:
    - `POST /register`: Chiama `authController.register`.
    - `POST /login`: Chiama `authController.login`.

### 7. Implementazione della Vista
- [ ] **Creare le viste HTML per la registrazione e il login:**
  - Creare `views/register.html`.
  - Creare `views/login.html`.
  - Aggiungere form per input `email` e `password`.

### 8. Scrittura dei Test
- [ ] **Scrivere test unitari per la logica di autenticazione:**
  - Creare `tests/authTests.js`.
  - Scrivere test per verificare:
    - Registrazione utente corretta.
    - Login con credenziali valide.
    - Rifiuto del login con credenziali errate.

### 9. Verifica e Debug
- [ ] **Testare l'intero flusso di autenticazione:**
  - Verificare registrazione e login tramite client Postman.
  - Debug del flusso completo.

### 10. Documentazione
- [ ] **Documentare il sistema di autenticazione:**
  - Aggiornare il file `README.md` con le istruzioni per l'uso del sistema di autenticazione.

Questo piano mira a fornire un'implementazione chiara e dettagliata di un sistema di autenticazione utente di base, facilitando l'integrazione e l'ulteriore espansione.