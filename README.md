# VARCAVIA Office - Autonomous Development System (MVP)

Questo repository contiene l'infrastruttura per **VARCAVIA Office**, un sistema di sviluppo software autonomo. Partendo da un obiettivo di business definito in `src/business_plan.yaml`, l'organizzazione di bot collabora per pianificare, sviluppare, testare e integrare il codice necessario per raggiungere l'obiettivo.

## Architettura

Il sistema è un'organizzazione di agenti IA specializzati:

-   **ManagerBot**: Il CEO. Orchestra il flusso di lavoro, delega i task e gestisce le Pull Request.
-   **ProjectBot**: Il CTO. Traduce gli obiettivi di business in piani tecnici dettagliati (`development_plan.md`).
-   **OperatorBot**: Lo Sviluppatore. Esegue i task tecnici, scrive codice e test, e apre le Pull Request.
-   **AuditBot**: Il Supervisore QA. Monitora lo stato del sistema e invia report.

## Setup e Attivazione

1.  **Progetto Google Cloud**: Un progetto con billing attivo e l'API Vertex AI (`aiplatform.googleapis.com`) abilitata.
2.  **Autenticazione**: Configurare Workload Identity Federation tra il repository GitHub e un Service Account GCP con il ruolo "Vertex AI User".
3.  **Segreti di GitHub**: In `Settings > Secrets and variables > Actions`, creare i seguenti segreti:
    * `BOT_GITHUB_TOKEN`: Un [Fine-grained personal access token](https://github.com/settings/tokens?type=beta) con permessi di lettura/scrittura su `Contents` e `Pull Requests`.
    * `EMAIL_*`: Le credenziali per le notifiche email (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USERNAME`, `EMAIL_PASSWORD`, `SENDER_EMAIL`, `RECEIVER_EMAIL`).
4.  **Missione**: Definire un task con `status: pending` nel file `src/business_plan.yaml`.
5.  **Attivazione**: Un `push` sul branch `main` attiverà il `ManagerBot` e darà inizio al ciclo.