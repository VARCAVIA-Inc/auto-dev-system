# ==============================================================================
# Makefile Unificato e Potenziato per il progetto VARCAVIA Office
#
# Questo file centralizza tutti i comandi comuni per lo sviluppo e il deployment,
# combinando la qualità del codice Go con il ciclo di vita completo per
# Protobuf, Docker e Kubernetes.
# ==============================================================================

# ----------------- Variabili di Configurazione -----------------
# Modifica questi valori per i futuri servizi.
IMAGE_NAME := varcavia/state-aggregator
IMAGE_TAG  := v0.1.0


# ----------------- Qualità del Codice & Dipendenze -----------------

## lint: Formatta e controlla la qualità del codice Go (go fmt, go vet).
.PHONY: lint
lint:
	@echo ">> Linting Go files..."
	@go fmt ./...
	@go vet ./...

## tidy: Pulisce e sistema le dipendenze del modulo Go.
.PHONY: tidy
tidy:
	@echo ">> Tidying Go module dependencies..."
	@go mod tidy


# ----------------- Generazione Codice Protobuf -----------------

## proto: Genera il codice Go dagli schemi Protobuf utilizzando buf.
.PHONY: proto
proto:
	@echo ">> Generating Protobuf Go code..."
	@cd schemas && buf generate && cd ..
	@echo "✅ Protobuf code generated successfully."


# ----------------- Ciclo di Vita Docker -----------------

## build: Costruisce l'immagine Docker per il state_aggregator_service.
.PHONY: build
build:
	@echo ">> Building Docker image: $(IMAGE_NAME):$(IMAGE_TAG)..."
	@docker build -t $(IMAGE_NAME):$(IMAGE_TAG) -f services/state_aggregator/Dockerfile .
	@echo "✅ Docker image built successfully."


# ----------------- Ciclo di Vita Kubernetes -----------------

## deploy: Applica i manifest Kubernetes per il state_aggregator.
.PHONY: deploy
deploy:
	@echo ">> Deploying state_aggregator to Kubernetes..."
	@kubectl apply -f k8s/state-aggregator-service.yaml
	@kubectl apply -f k8s/state-aggregator-deployment.yaml
	@echo "✅ Service deployed. Run 'kubectl get pods' to check status."

## undeploy: Rimuove le risorse del state_aggregator da Kubernetes.
.PHONY: undeploy
undeploy:
	@echo ">> Removing state_aggregator from Kubernetes..."
	@kubectl delete -f k8s/state-aggregator-deployment.yaml --ignore-not-found=true
	@kubectl delete -f k8s/state-aggregator-service.yaml --ignore-not-found=true
	@echo "✅ Service undeployed."

## k8s-dna-configmap: Crea il ConfigMap 'varcavia-dna' dai file nella cartella /dna.
.PHONY: k8s-dna-configmap
k8s-dna-configmap:
	@echo ">> Creating/Updating 'varcavia-dna' ConfigMap..."
	@kubectl create configmap varcavia-dna --from-file=./dna -o yaml --dry-run=client | kubectl apply -f -
	@echo "✅ ConfigMap 'varcavia-dna' applied."
	
# ----------------- Aiuto -----------------

## help: Mostra questo messaggio di aiuto auto-documentante.
.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

