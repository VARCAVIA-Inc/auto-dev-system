package main

import (
    "context"
    "log"

    corev1 "services/gen/go/core/v1"
    "services/internal/kafka"
)

func main() {
    ctx := context.Background()
    handler := func(obj *corev1.Objective) {
        // Construct a simple blueprint for each objective
        bp := &corev1.Blueprint{
            Id:         "bp-" + obj.Id,
            ObjectiveId: obj.Id,
            Tasks: []*corev1.Task{
                {
                    Id:   "task1",
                    Type: "noop",
                    // Leaving Payload nil for simplicity
                },
            },
        }
        if err := kafka.Produce("varcavia.blueprints", bp); err != nil {
            log.Printf("failed to produce blueprint: %v", err)
        } else {
            log.Printf("produced blueprint for objective %s", obj.Id)
        }
    }

    if err := kafka.Consume[*corev1.Objective](ctx, "varcavia.objectives", "architect-service-group", handler); err != nil {
        log.Fatalf("error consuming objectives: %v", err)
    }
}
