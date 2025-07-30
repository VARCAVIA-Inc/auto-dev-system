package kafka

// Package kafka provides convenience wrappers around the Confluent Kafka Go
// client. These wrappers encapsulate common configuration and
// serialization concerns so that services in the VARCAVIA Office project
// can publish messages to Kafka topics without duplicating boilerplate.

import (
    "github.com/confluentinc/confluent-kafka-go/v2/kafka"
    "google.golang.org/protobuf/proto"
)

// Produce serializes a Protobuf message and publishes it to the provided
// topic. The broker address is fixed to the internal Strimzi cluster and
// the producer is closed after the message is flushed. If any error occurs
// during construction of the producer, serialization or publication the
// error is returned so the caller may handle retries or dead-lettering.
func Produce(topic string, message proto.Message) error {
    // In a production environment the broker endpoint should be injected via
    // configuration or environment variables. For the MVP we rely on the
    // Strimzi default service name resolved via Kubernetes DNS.
    producer, err := kafka.NewProducer(&kafka.ConfigMap{
        "bootstrap.servers": "kafka-broker.kafka.svc.cluster.local:9092",
    })
    if err != nil {
        return err
    }
    defer producer.Close()

    // Serialize the Protobuf message into a binary payload. The
    // google.golang.org/protobuf/proto package provides efficient
    // marshalling for all generated message types.
    binaryData, err := proto.Marshal(message)
    if err != nil {
        return err
    }

    // Deliver the message asynchronously. The underlying library will
    // handle partition assignment. We do not set a key so messages are
    // balanced across partitions.
    err = producer.Produce(&kafka.Message{
        TopicPartition: kafka.TopicPartition{Topic: &topic, Partition: kafka.PartitionAny},
        Value:          binaryData,
    }, nil)
    if err != nil {
        return err
    }

    // Block until all outstanding messages are delivered or up to
    // 15 seconds. This ensures at-least-once semantics for the caller.
    producer.Flush(15 * 1000)
    return nil
}
