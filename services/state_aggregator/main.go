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
	"google.golang.org/grpc/reflection"
	"google.golang.org/grpc/status"

	pb "varcavia.com/sentient-organism/services/gen/go/state_aggregator/v1"
)

// server implementa l'interfaccia gRPC generata
type server struct {
	pb.UnimplementedStateAggregatorServiceServer
	redisClient *redis.Client
}

// NewServer crea un nuovo server con client Redis configurato
func NewServer() *server {
	redisAddr := os.Getenv("REDIS_ADDR")
	if redisAddr == "" {
		redisAddr = "localhost:6379"
	}

	rdb := redis.NewClient(&redis.Options{Addr: redisAddr})

	if _, err := rdb.Ping(context.Background()).Result(); err != nil {
		log.Fatalf("Impossibile connettersi a Redis: %v", err)
	}

	log.Printf("Connessione a Redis stabilita con successo a %s", redisAddr)
	return &server{redisClient: rdb}
}

// SetTaskState salva lo stato di un task in Redis
func (s *server) SetTaskState(ctx context.Context, req *pb.SetTaskStateRequest) (*pb.SetTaskStateResponse, error) {
	state := req.GetState()
	if state == nil || state.TaskId == "" {
		return nil, status.Error(codes.InvalidArgument, "State o TaskId vuoti")
	}

	key := fmt.Sprintf("task_state:%s", state.TaskId)

	pipe := s.redisClient.TxPipeline()
	pipe.HSet(ctx, key, map[string]interface{}{
		"status":      state.Status.String(),
		"worker_id":   state.WorkerId,
		"last_update": time.Now().UTC().Format(time.RFC3339),
		"details":     state.Details,
	})
	pipe.Expire(ctx, key, 24*time.Hour)

	if _, err := pipe.Exec(ctx); err != nil {
		log.Printf("Errore Redis per task %s: %v", state.TaskId, err)
		return nil, status.Error(codes.Internal, "Impossibile aggiornare lo stato")
	}

	return &pb.SetTaskStateResponse{Success: true, TaskId: state.TaskId}, nil
}

// GetTaskState recupera lo stato di un task da Redis
func (s *server) GetTaskState(ctx context.Context, req *pb.GetTaskStateRequest) (*pb.GetTaskStateResponse, error) {
	taskID := req.GetTaskId()
	if taskID == "" {
		return nil, status.Error(codes.InvalidArgument, "TaskId vuoto")
	}

	key := fmt.Sprintf("task_state:%s", taskID)
	val, err := s.redisClient.HGetAll(ctx, key).Result()
	if err != nil && err != redis.Nil {
		log.Printf("Errore Redis per task %s: %v", taskID, err)
		return nil, status.Error(codes.Internal, "Errore database")
	}
	if len(val) == 0 {
		return nil, status.Errorf(codes.NotFound, "Nessuno stato per task %s", taskID)
	}

	statusVal, ok := pb.Status_value[val["status"]]
	if !ok {
		return nil, status.Error(codes.Internal, "Stato non valido salvato")
	}

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
		port = "50051"
	}

	lis, err := net.Listen("tcp", fmt.Sprintf(":%s", port))
	if err != nil {
		log.Fatalf("Impossibile mettersi in ascolto sulla porta %s: %v", port, err)
	}

	grpcServer := grpc.NewServer()
	pb.RegisterStateAggregatorServiceServer(grpcServer, NewServer())

	// Health check per Kubernetes
	healthServer := health.NewServer()
	grpc_health_v1.RegisterHealthServer(grpcServer, healthServer)
	healthServer.SetServingStatus("", grpc_health_v1.HealthCheckResponse_SERVING)

	// Reflection per debug con grpcurl
	reflection.Register(grpcServer)

	// Avvio server
	go func() {
		log.Printf("✅ Server gRPC in ascolto su %v", lis.Addr())
		if err := grpcServer.Serve(lis); err != nil {
			log.Fatalf("Server gRPC terminato: %v", err)
		}
	}()

	// Graceful shutdown
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)
	<-stop

	log.Println("🔴 Shutdown server gRPC...")
	grpcServer.GracefulStop()
	log.Println("✅ Server gRPC spento correttamente")
}
