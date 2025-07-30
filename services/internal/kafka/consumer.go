package kafka

import (
    "context"
    "time"
    "github.com/confluentinc/confluent-kafka-go/v2/kafka"
    "google.golang.org/protobuf/proto"
)

// HandlerFunc defines a callback to process a protobuf message.
type HandlerFunc[M proto.Message] func(message M) error

// Consume subscribes to the given Kafka topic and invokes the handler for each received message.
// It uses generics to unmarshal protobuf messages of type M and runs until the context is cancelled.
func Consume[M proto.Message](ctx context.Context, topic string, groupID string, handler HandlerFunc[M]) error {
    consumer, err := kafka.NewConsumer(&kafka.ConfigMap{
        "bootstrap.servers": getKafkaBroker(),
        "group.id":          groupID,
        "auto.offset.reset": "earliest",
    })
    if err != nil {
        return err
    }
    defer consumer.Close()

    if err := consumer.SubscribeTopics([]string{topic}, nil); err != nil {
        return err
    }

    for {
        select {
        case <-ctx.Done():
            return nil
        default:
            msg, err := consumer.ReadMessage(1 * time.Second)
            if err != nil {
                // Continue on timeouts
                if kafkaErr, ok := err.(kafka.Error); ok && kafkaErr.IsTimeout() {
                    continue
                }
              // Unmarshal the protobuf message into a new instance of M
            m := new(M)
            if err := proto.Unmarshal(msg.Value, m); err != nil {
                // Skip invalid messages and continue consuming
                continue
            }
            // Invoke the handler; ignore handler error
            _ = handler(*m)
gnore handler errors for now
            _ = handler(m)
        }
    }
}
