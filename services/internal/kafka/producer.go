package kafka

import (
    "os"
    "github.com/confluentinc/confluent-kafka-go/v2/kafka"
    "google.golang.org/protobuf/proto"
)

// Produce publishes a protobuf message to the given Kafka topic using the default broker.
func Produce(topic string, message proto.Message) error {
    producer, err := kafka.NewProducer(&kafka.ConfigMap{"bootstrap.servers": getKafkaBroker()})
    if err != nil {
        return err
    }
    defer producer.Close()

    // Serialize the protobuf message to bytes
    data, err := proto.Marshal(message)
    if err != nil {
        return err
    }

    deliveryChan := make(chan kafka.Event, 1)
    // Produce the message asynchronously
    if err := producer.Produce(&kafka.Message{
        TopicPartition: kafka.TopicPartition{Topic: &topic, Partition: kafka.PartitionAny},
        Value:          data,
    }, deliveryChan); err != nil {
        return err
    }

    // Wait for delivery report
    e := <-deliveryChan
    m := e.(*kafka.Message)
    close(deliveryChan)
    if m.TopicPartition.Error != nil {
        return m.TopicPartition.Error
    }

    return nil
}

// getKafkaBroker returns the Kafka bootstrap server from environment or default value.
func getKafkaBroker() string {
    if broker := os.Getenv("KAFKA_BROKER"); broker != "" {
        return broker
    }
    return "kafka-broker.kafka.svc.cluster.local:9092"
}
