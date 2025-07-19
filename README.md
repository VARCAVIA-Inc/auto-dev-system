# VARCAVIA Office – Autonomous Development System (MVP)

> **Fast start**
>
> 1. Abilita **Generative AI** in Vertex AI Studio sul progetto Google Cloud.
> 2. Avvia Codespace e lancia `./scripts/vertex_check.sh`.
> 3. Se il ping risponde “Pong!”, sei operativo.

Questo repository contiene l'infrastruttura per **VARCAVIA Office**, un sistema di sviluppo software autonomo. Partendo da un obiettivo di business definito in `business_plan.yaml`, un gruppo di bot collabora per pianificare, sviluppare e committare il codice necessario per raggiungere l'obiettivo.

## Architettura

Il sistema è composto da bot specializzati, ognuno con un ruolo preciso:

* **ManagerBot** (C-level strategist) – legge `business_plan.yaml`, orchestra il flusso di lavoro e delega compiti.
* **ProjectBot** (CTO) – riceve l’obiettivo business e crea un piano tecnico dettagliato (`development_plan.md`).
* **OperatorBot** (Developer) – esegue i task tecnici: scrive codice, esegue comandi, apre PR.
* **AuditBot** (QA Supervisor) – analizza qualità, costi e coerenza, fornendo feedback al ManagerBot.

## Attivazione & Setup

1. **Configura Google Cloud**

   * Crea (o usa) un progetto con billing attivo.
   * Abilita l’API **Vertex AI** (`aiplatform.googleapis.com`).
   * **Passo critico:** in Vertex AI Studio clicca **Enable Generative AI Tools**. Senza questo “feature flag” i modelli Gemini restano invisibili.
2. **Crea le risorse cloud**

   * Service Account: `vertex-client@<project>.iam.gserviceaccount.com` con `roles/aiplatform.user`.
   * Workload Identity Pool & Provider collegati a GitHub, con i ruoli `iam.workloadIdentityUser` e `iam.serviceAccountTokenCreator`.
3. **Aggiorna i workflow GitHub Actions**

   * Inserisci `project_number`, `project_id`, e l’email della Service Account nei file `.github/workflows/*.yml`.
4. **Crea il segreto GitHub**

   * Fine‑grained PAT con accesso `Contents`+`Pull Requests`. Salvalo come `BOT_GITHUB_TOKEN`.
5. **Configura Codespace**

   * Esegui lo script di setup:

     ```bash
     sudo apt-get update && sudo apt-get --only-upgrade install -y google-cloud-cli
     ./scripts/vertex_auth_config.sh   # crea/patcha ADC e impersonazione SA
     ./scripts/vertex_check.sh         # health‑check completo
     ```
6. **Definisci la missione**

   * Modifica `src/business_plan.yaml` per impostare il primo obiettivo.
7. **Push**

   * Commit & push su `main` → parte il ManagerBot.

## Script utili

* `scripts/vertex_auth_config.sh` – login, patch ADC con `quota_project_id`, set SA impersonation.
* `scripts/vertex_check.sh` – stampa lo stato API, controlla i modelli Gemini disponibili, esegue un test `generateContent`.

## FAQ lampo

| Domanda                                         | Risposta                                                                 |
| ----------------------------------------------- | ------------------------------------------------------------------------ |
| Perché vedo 404 su `/publishers/google/models`? | Non hai cliccato **Enable Generative AI** sul progetto.                  |
| Perché `:predict` fallisce?                     | Gemini usa i nuovi metodi `:generateContent` / `:streamGenerateContent`. |
| La CLI non riconosce `publisher-models`         | Aggiorna a **gcloud ≥ 530** oppure usa la REST.                          |

---

© 2025 Varcavia Inc. Tutti i diritti riservati.
