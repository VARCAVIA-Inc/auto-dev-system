package main

import (
	"context"
	"log"

	ceopb "varcavia.com/sentient-organism/services/gen/go/ceo_service/v1"
	archpb "varcavia.com/sentient-organism/services/gen/go/architect_service/v1"
	"varcavia.com/sentient-organism/services/internal/kafka"

	ckafka "github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/types/known/structpb"
)

const (
	inTopic  = "ceo_objectives"
	outTopic = "architect_blueprints"
)

func main() {
	ctx := context.Background()
	groupID := "architect-service-group"

	err := kafka.Consume(ctx, inTopic, groupID, handleObjective)
	if err != nil && err != context.Canceled {
		log.Fatalf("consumer error: %v", err)
	}
}

func handleObjective(msg *ckafka.Message) error {
	var obj ceopb.Objective
	if err := proto.Unmarshal(msg.Value, &obj); err != nil {
		log.Printf("invalid Objective: %v", err)
		return nil // skip message
	}

	doc, _ := structpb.NewStruct(map[string]interface{}{
		"tasks": []interface{}{
			map[string]interface{}{
				"type": "echo",
				"data": obj.Description,
			},
		},
	})

	blue := &archpb.TechnicalBlueprint{
		Id:          obj.Id + "-BP-001",
		ObjectiveId: obj.Id,
		Doc:         doc,
	}

	if err := kafka.Produce(outTopic, blue); err != nil {
		log.Printf("kafka produce error: %v", err)
		return err
	}

	log.Printf("✅ blueprint %s pubblicato", blue.Id)
	return nil
}
