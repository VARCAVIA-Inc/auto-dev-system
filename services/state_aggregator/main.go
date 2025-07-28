package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/redis/go-redis/v9"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/health"
	"google.golang.org/grpc/health/grpc_health_v1"
	"google.golang.org/grpc/status"

	// Importa il package Go generato da Protobuf.
	// Assicurati che il percorso corrisponda a quello nel tuo go.mod.
	pb "varcavia.com/sentient-organism/services/gen/go/state_aggregator/v1"
)

// server struct implementa l'interfaccia gRPC generata.
// Contiene un client Redis per interagire con il database.
type server struct {
	pb.UnimplementedStateAggregatorServiceServer // Necessario per la compatibilità futura.
	redisClient *redis.Client
}

// NewServer crea una nuova istanza del nostro server con un client Redis configurato.
func NewServer() *server {
	redisAddr := os.Getenv("REDIS_ADDR")
	if redisAddr == "" {
		redisAddr = "localhost:6379" // Fallback per lo sviluppo locale. [cite: 61]
	}

	rdb := redis.NewClient(&redis.Options{
		Addr: redisAddr,
	})

	// Testa la connessione a Redis all'avvio.
	if _, err := rdb.Ping(context.Background()).Result(); err != nil {
		log.Fatalf("Impossibile connettersi a Redis: %v", err)
	}

	log.Printf("Connessione a Redis stabilita con successo a %s", redisAddr)
	return &server{redisClient: rdb}
}

// SetTaskState implementa la logica per salvare lo stato di un task in Redis.
func (s *server) SetTaskState(ctx context.Context, req *pb.SetTaskStateRequest) (*pb.SetTaskStateResponse, error) {
	state := req.GetState()
	if state == nil || state.TaskId == "" {
		return nil, status.Error(codes.InvalidArgument, "L'oggetto State o il TaskId non possono essere vuoti")
	}

	key := fmt.Sprintf("task_state:%s", state.TaskId)

	// Utilizziamo una pipeline per eseguire i comandi HSet e Expire in modo atomico.
	pipe := s.redisClient.TxPipeline()
	pipe.HSet(ctx, key, map[string]interface{}{
		"status":      state.Status.String(),
		"worker_id":   state.WorkerId,
		"last_update": time.Now().UTC().Format(time.RFC3339),
		"details":     state.Details,
	})
	pipe.Expire(ctx, key, 24*time.Hour) // Imposta una TTL di 24 ore per pulizia automatica.
	if _, err := pipe.Exec(ctx); err != nil {
		log.Printf("Errore durante l'aggiornamento dello stato su Redis per il task %s: %v", state.TaskId, err)
		return nil, status.Error(codes.Internal, "Impossibile aggiornare lo stato nel database")
	}

	return &pb.SetTaskStateResponse{Success: true, TaskId: state.TaskId}, nil
}

// GetTaskState implementa la logica per recuperare lo stato di un task da Redis.
func (s *server) GetTaskState(ctx context.Context, req *pb.GetTaskStateRequest) (*pb.GetTaskStateResponse, error) {
	taskID := req.GetTaskId()
	if taskID == "" {
		return nil, status.Error(codes.InvalidArgument, "Il TaskId non può essere vuoto")
	}

	key := fmt.Sprintf("task_state:%s", taskID)
	val, err := s.redisClient.HGetAll(ctx, key).Result()

	if err != nil {
		if err == redis.Nil {
			return nil, status.Errorf(codes.NotFound, "Nessuno stato trovato per il task ID: %s", taskID)
		}
		log.Printf("Errore durante il recupero dello stato da Redis per il task %s: %v", taskID, err)
		return nil, status.Error(codes.Internal, "Impossibile recuperare lo stato dal database")
	}
	
	if len(val) == 0 {
		return nil, status.Errorf(codes.NotFound, "Nessuno stato trovato per il task ID: %s", taskID)
	}

	statusVal, ok := pb.Status_value[val["status"]]
	if !ok {
		return nil, status.Error(codes.Internal, "Stato non valido recuperato dal database")
	}

	// La conversione del timestamp non è inclusa per semplicità, ma andrebbe gestita.
	return &pb.GetTaskStateResponse{
		State: &pb.TaskState{
			TaskId:   taskID,
			Status:   pb.Status(statusVal),
			WorkerId: val["worker_id"],
			Details:  val["details"],
		},
	}, nil
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "50051" // Porta di default per gRPC.
	}

	lis, err := net.Listen("tcp", fmt.Sprintf(":%s", port))
	if err != nil {
		log.Fatalf("Impossibile mettersi in ascolto sulla porta %s: %v", port, err)
	}

	// Creazione del server gRPC e registrazione dei servizi
	grpcServer := grpc.NewServer()
	pb.RegisterStateAggregatorServiceServer(grpcServer, NewServer())
	
	// Registrazione del servizio di Health Check (fondamentale per Kubernetes)
	healthServer := health.NewServer()
	grpc_health_v1.RegisterHealthServer(grpcServer, healthServer)
	healthServer.SetServingStatus("state_aggregator", grpc_health_v1.HealthCheckResponse_SERVING)


	// Avvio del server in una goroutine separata
	go func() {
		log.Printf("✅ Server gRPC in ascolto su %v", lis.Addr())
		if err := grpcServer.Serve(lis); err != nil {
			log.Fatalf("Impossibile avviare il server: %v", err)
		}
	}()

	// Setup per il graceful shutdown
	stopChan := make(chan os.Signal, 1)
	signal.Notify(stopChan, syscall.SIGINT, syscall.SIGTERM)

	// Blocco fino alla ricezione del segnale
	<-stopChan
	
	log.Println("🔴 Inizio procedura di shutdown del server gRPC...")
	
	// Tentativo di graceful stop
	grpcServer.GracefulStop()
	
	log.Println("✅ Server gRPC spento correttamente.")
}