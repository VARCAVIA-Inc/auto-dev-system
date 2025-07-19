# VARCAVIA Office - Autonomous Development System (MVP)

Questo repository contiene l'infrastruttura per **VARCAVIA Office**, un sistema di sviluppo software autonomo. Partendo da un obiettivo di business definito in un file `business_plan.yaml`, l'organizzazione di bot collabora per pianificare, sviluppare, e committare il codice necessario per raggiungere l'obiettivo.

## Architettura

Il sistema è composto da un'organizzazione di bot specializzati, ognuno con un ruolo definito:

-   **ManagerBot**: Il CEO strategico. Legge il `business_plan.yaml`, orchestra il flusso di lavoro e delega i compiti agli altri bot.
-   **ProjectBot**: Il CTO. Riceve un obiettivo di business dal ManagerBot e lo traduce in un piano di sviluppo tecnico dettagliato (`development_plan.md`).
-   **OperatorBot**: Lo Sviluppatore. Riceve un singolo task tecnico dal ManagerBot (preso dal piano di sviluppo) e lo esegue: scrive codice, esegue comandi e crea Pull Request.
-   **AuditBot**: Il Supervisore QA. In futuro, analizzerà la qualità, i costi e la coerenza del lavoro svolto, fornendo feedback strategico al ManagerBot.

## Attivazione

1.  **Configura Google Cloud**: Assicurati di avere un progetto Google Cloud con un account di fatturazione attivo e l'API Vertex AI (`aiplatform.googleapis.com`) abilitata.
2.  **Crea le Risorse**: Segui le istruzioni per creare il Service Account e il Workload Identity Pool, come fatto in precedenza.
3.  **Aggiorna i Workflow**: Inserisci i tuoi ID corretti (`project_number`, `project_id`, `service_account`) nei file `.github/workflows/*.yml`.
4.  **Crea il Segreto GitHub**: Crea un [Fine-grained personal access token](https://github.com/settings/tokens?type=beta) con permessi di lettura/scrittura su `Contents` e `Pull Requests` per questo repository. Salvalo nei segreti del repository con il nome `BOT_GITHUB_TOKEN`.
5.  **Definisci la Missione**: Modifica `src/business_plan.yaml` per definire il primo task del tuo progetto.
6.  **Push**: Fai un push sul branch `main` per attivare il ManagerBot.