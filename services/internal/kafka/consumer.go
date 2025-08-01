package kafka

import (
    "context"
    ckafka "github.com/confluentinc/confluent-kafka-go/v2/kafka"
)

// Consume si sottoscrive al topic indicato e, per ogni messaggio,
// invoca il callback handler. L’esecuzione si interrompe quando il
// contesto viene cancellato.
func Consume(ctx context.Context, topic string, groupID string, handler func(*ckafka.Message) error) error {
    c, err := ckafka.NewConsumer(&ckafka.ConfigMap{
        "bootstrap.servers": "kafka-broker.kafka.svc.cluster.local:9092",
        "group.id":          groupID,
        "auto.offset.reset": "earliest",
    })
    if err != nil {
        return err
    }
    defer c.Close()

    if err := c.SubscribeTopics([]string{topic}, nil); err != nil {
        return err
    }

    for {
        select {
        case <-ctx.Done():
            return ctx.Err()
        default:
            msg, err := c.ReadMessage(-1)
            if err != nil {
                // Log o gestisci l'errore, poi continua
                continue
            }
            if err := handler(msg); err != nil {
                // L'handler ha fallito; loggare o inviare su una DLQ
                continue
            }
        }
    }
}
