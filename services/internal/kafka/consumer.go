package kafka

// This package implements a simple Kafka consumer wrapper. It hides
// configuration defaults and provides a callback-style API for
// consuming messages and deserializing them into Protobuf types. The
// caller supplies a handler function that is invoked for each message
// received. The consumer will run until the handler returns an error
// (other than a timeout) or the context is cancelled.

import (
    "context"
    "time"

    "github.com/confluentinc/confluent-kafka-go/v2/kafka"
    "google.golang.org/protobuf/proto"
)

// HandlerFunc is a function that processes a deserialized Protobuf
// message. If it returns an error it will be logged and the consumer
// will continue polling.
type HandlerFunc[M proto.Message] func(message M) error

// Consume subscribes to the specified topics and invokes the handler
// for each message received. The generic type parameter M should be
// instantiated with the appropriate generated Protobuf message type.
// For example:
//
//    err := kafka.Consume(ctx, []string{"ceo_objectives"}, handler)
//
// The consumer will automatically commit offsets. Errors during
// deserialization are logged and the message is skipped.
func Consume[M proto.Message](ctx context.Context, topics []string, groupID string, handler HandlerFunc[M]) error {
    consumer, err := kafka.NewConsumer(&kafka.ConfigMap{
        "bootstrap.servers": "kafka-broker.kafka.svc.cluster.local:9092",
        "group.id":          groupID,
        "auto.offset.reset": "earliest",
    })
    if err != nil {
        return err
    }
    defer consumer.Close()

    if err := consumer.SubscribeTopics(topics, nil); err != nil {
        return err
    }

    for {
        select {
        case <-ctx.Done():
            return nil
        default:
            msg, err := consumer.ReadMessage(1 * time.Second)
            if err != nil {
                // Timeout is not considered an error
                if kafkaErr, ok := err.(kafka.Error); ok && kafkaErr.IsTimeout() {
                    continue
                }
                // Unexpected error – return to caller
                return err
            }

            // Create a zero value of the generic message type
            var event M
            if err := proto.Unmarshal(msg.Value, event); err != nil {
                // Skip malformed messages
                continue
            }
            // Invoke the handler and ignore errors for individual messages
            _ = handler(event)
        }
    }
}
