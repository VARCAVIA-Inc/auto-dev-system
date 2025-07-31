### Backlog di Implementazione – VARCAVIA Office

- [ ] **Configurazione repository:** impostare branch protection su `main` con 2 approvazioni e status check obbligatori (`ci-lint-and-test`, `ci-security-scan`, `dna-validation`).  
- [ ] **Template PR:** creare `.github/pull_request_template.md` con sezione descrizione, riferimento Jira, tipi di modifica e checklist.  
- [ ] **Security scanning:** aggiungere workflow CI per scansione SBOM e linter di sicurezza.  
- [ ] **ConfigMap DNA:** aggiungere manifest/Script per creare `varcavia-dna` da cartella `dna/` e installare l’operatore Stakater Reloader per hot‑reload.  
- [ ] **Kafka infrastructure:** definire `schemas/v1/` per i servizi (ceo, architect, worker, auditor) con `buf.gen.yaml`; implementare un package `internal/kafka` con wrapper producer/consumer come nel piano; aggiungere manifest Strimzi per cluster Kafka.  
- [ ] **Istio/OPA:** creare `mtls-strict.yaml` per mTLS, definire workflow cosign per firmare le immagini e template Gatekeeper per la verifica.  
- [ ] **ceo_service:** sviluppare un micro‑servizio Go che legge `business_mission.yaml`, pubblica messaggi `Objective` su Kafka, integra l’API di Gemini (versione deterministica e AI‑powered), effettua chiamata di validazione all’auditor_service e implementa il quorum con cost_optimizer_service.  
- [ ] **architect_service:** sviluppare consumer Kafka che riceve `Objective` e genera `TechnicalBlueprint`, stimando costi via cost_optimizer_service e validando le decisioni con auditor_service; pubblicare tasks su Kafka.  
- [ ] **worker_pool:** implementare un dispatcher Go con mappa di funzioni per eseguire task; integrare Prometheus per telemetria.  
- [ ] **auditor_service:** caricare policy OPA (es. `ethical_boundaries.rego`), implementare AI Safety gating (es. LlamaGuard) e circuito di fuzzing; esporre RPC di validazione decisioni.  
- [ ] **knowledge_graph_populator:** consumare eventi da Kafka e inserire nodi in Neo4j tramite query Cypher; creare topic `system_events`.  
- [ ] **cost_optimizer_service:** integrare API dei provider cloud per stimare costi LLM, implementare circuit breaker e regole FinOps.  
- [ ] **Helm umbrella chart:** creare `genesis-as-a-service` con dipendenze configurabili e test multi‑tenant.  
- [ ] **Governance:** implementare il `Council of Services` con interfacce gRPC per quorum e registrare nel codice la logica del RL Smart Advisor e del motore di evoluzione.  

