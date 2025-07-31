package main

import (
    "fmt"
    "log"
    "os"

    yaml "gopkg.in/yaml.v3"

    ceopb "varcavia.com/sentient-organism/services/gen/go/ceo_service/v1"
    "varcavia.com/sentient-organism/services/internal/config"
    "varcavia.com/sentient-organism/services/internal/kafka"
)

func main() {
    dnaPath := "/app/dna/business_mission.yaml"
    if envPath := os.Getenv("DNA_PATH"); envPath != "" {
        dnaPath = envPath
    }

    data, err := os.ReadFile(dnaPath)
    if err != nil {
        log.Fatalf("errore nella lettura del DNA: %v", err)
    }

    var mission config.BusinessMission
    if err := yaml.Unmarshal(data, &mission); err != nil {
        log.Fatalf("DNA non valido: %v", err)
    }

    objective := &ceopb.Objective{
        Id:          fmt.Sprintf("%s-OBJ-001", mission.MissionID),
        Description: mission.Description,
    }

    if err := kafka.Produce("ceo_objectives", objective); err != nil {
        log.Fatalf("Errore nella pubblicazione su Kafka: %v", err)
    }

    log.Println("✅ CEO service ha pubblicato l'obiettivo con successo")
}
