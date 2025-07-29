# ==============================================================================
# Makefile Unificato e Potenziato per il progetto VARCAVIA Office
# ==============================================================================

# ----------------- Variabili di Configurazione -----------------
IMAGE_NAME := varcavia/state-aggregator
IMAGE_TAG  := v0.1.0

# ----------------- Qualità del Codice & Dipendenze -----------------

## lint: formatta e controlla la qualità del codice Go
.PHONY: lint
lint:
	@echo ">> Linting Go files..."
	go fmt ./...
	go vet ./...

## tidy: pulisce e sistema le dipendenze del modulo Go
.PHONY: tidy
tidy:
	@echo ">> Tidying Go module dependencies..."
	go mod tidy

# ----------------- Generazione Codice Protobuf -----------------

## proto: genera il codice Go dagli schemi Protobuf
.PHONY: proto
proto:
	@echo ">> Generating Protobuf Go code..."
	cd schemas && buf generate && cd ..
	@echo "✅ Proto OK"

# ----------------- Test -----------------

## test: vet + unit test (dipende da proto per avere i .pb.go aggiornati)
.PHONY: test
test: proto
	go vet ./...
	go test ./...

# ----------------- Ciclo di Vita Docker -----------------

## build: costruisce l'immagine Docker
# dipende da proto per garantire che il codice generato sia aggiornato
.PHONY: build
build: proto
	@echo ">> Building Docker image: $(IMAGE_NAME):$(IMAGE_TAG)..."
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) -f services/state_aggregator/Dockerfile .
	@echo "✅ Image OK"

# ----------------- Ciclo di Vita Kubernetes -----------------

## deploy: applica i manifest Kubernetes per il servizio
.PHONY: deploy
deploy:
	@echo ">> Deploying state_aggregator to Kubernetes..."
	kubectl apply -f k8s/state-aggregator-service.yaml
	kubectl apply -f k8s/state-aggregator-deployment.yaml
	@echo "✅ Deployed. Run 'kubectl get pods' to check status."

## undeploy: rimuove le risorse Kubernetes del servizio
.PHONY: undeploy
undeploy:
	@echo ">> Removing state_aggregator from Kubernetes..."
	kubectl delete -f k8s/state-aggregator-deployment.yaml --ignore-not-found=true
	kubectl delete -f k8s/state-aggregator-service.yaml --ignore-not-found=true
	@echo "✅ Service undeployed."

# ----------------- Aiuto -----------------

## help: mostra questo messaggio di aiuto
.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'
