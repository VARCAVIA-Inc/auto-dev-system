package kafka

// Package kafka for internal helpers to interact with Kafka using the
// confluentinc client.  This wrapper centralises connection logic and
// Protobuf serialization so that producers throughout the codebase can
// publish messages without duplicating boilerplate.

import (
    "context"
    "time"

    ckafka "github.com/confluentinc/confluent-kafka-go/v2/kafka"
    "google.golang.org/protobuf/proto"
)

// Produce serializes the given Protobuf message and publishes it to the
// specified topic.  It returns nil on success or an error if the
// message could not be sent.  The producer is created and closed
// within the scope of this call; for high‑throughput use cases
// consider maintaining a long‑lived producer instance instead.
func Produce(topic string, message proto.Message) error {
    // Configure the producer to talk to the internal broker.  The
    // address should be injected via environment variables in the
    // future to avoid hard‑coding, but a sensible default is
    // provided here to aid local development.
    cfg := &ckafka.ConfigMap{
        "bootstrap.servers": "kafka-broker.kafka.svc.cluster.local:9092",
    }
    p, err := ckafka.NewProducer(cfg)
    if err != nil {
        return err
    }
    defer p.Close()

    // Marshal the message into binary using Protobuf.
    value, err := proto.Marshal(message)
    if err != nil {
        return err
    }

    // Create the Kafka message.  PartitionAny allows Kafka to
    // determine the partition based on its configured partitioner.
    kmsg := &ckafka.Message{
        TopicPartition: ckafka.TopicPartition{Topic: &topic, Partition: ckafka.PartitionAny},
        Value:          value,
    }

    // Produce the message asynchronously.
    if err := p.Produce(kmsg, nil); err != nil {
        return err
    }

    // Wait up to 15 seconds for any outstanding messages to be sent to
    // the broker.  A zero return value from Flush indicates that all
    // messages have been delivered.
    remaining := p.Flush(int(15 * time.Second / time.Millisecond))
    if remaining > 0 {
        return context.DeadlineExceeded
    }
    return nil
}
