# ---------- STAGE 1: build ----------
FROM golang:1.24-alpine AS builder

# 1. Tools: health‑probe, protoc‑gen‑go, protoc‑gen‑go‑grpc, buf
RUN apk add --no-cache curl \
 && curl -L https://github.com/grpc-ecosystem/grpc-health-probe/releases/download/v0.4.26/grpc_health_probe-linux-amd64 \
      -o /bin/grpc-health-probe \
 && chmod +x /bin/grpc-health-probe \
 && go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.34.0 \
 && go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.4.0 \
 && go install github.com/bufbuild/buf/cmd/buf@v1.30.0

WORKDIR /app

# 2. Mod Go e deps
COPY go.mod go.sum ./
RUN go mod download

# 3. Sorgenti (inclusi .proto e buf.*)
COPY . .

# 4. Aggiorna mod protos e genera codice
RUN cd schemas && buf mod update && buf generate && cd /app

# 5. Compila il binario
RUN CGO_ENABLED=0 GOOS=linux go build \
      -a -installsuffix cgo -ldflags "-s -w" \
      -o /app/build/state_aggregator \
      ./services/state_aggregator

# ---------- STAGE 2: runtime ----------
FROM scratch
WORKDIR /app

COPY --from=builder /app/build/state_aggregator .
COPY --from=builder /bin/grpc-health-probe /bin/grpc-health-probe
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

EXPOSE 50051
ENTRYPOINT ["/app/state_aggregator"]