package main

import (
    "log"
    "os"

    "varcavia.com/sentient-organism/services/internal/config"
    "varcavia.com/sentient-organism/services/internal/kafka"
    pb "varcavia.com/sentient-organism/services/gen/go/core/v1"
    "gopkg.in/yaml.v3"
)

// main is the entrypoint for the ceo_service.
// It reads the business mission from a YAML file, constructs an Objective
// message and publishes it to Kafka on the objectives topic.
func main() {
    // Determine path to business mission YAML; allow override via env var
    path := os.Getenv("BUSINESS_MISSION_PATH")
    if path == "" {
        path = "dna/business_mission.yaml"
    }
    data, err := os.ReadFile(path)
    if err != nil {
        log.Fatalf("failed to read business mission file: %v", err)
    }

    // Unmarshal YAML into our config struct
    var mission config.BusinessMission
    if err := yaml.Unmarshal(data, &mission); err != nil {
        log.Fatalf("failed to unmarshal business mission: %v", err)
    }

    // Map mission to a protobuf Objective
    objective := &pb.Objective{
        Id:          mission.MissionID,
        Description: mission.Description,
    }

    // Produce the objective to Kafka
    if err := kafka.Produce("varcavia.objectives", objective); err != nil {
        log.Fatalf("failed to publish objective: %v", err)
    }

    log.Printf("published objective %s", objective.Id)
}
