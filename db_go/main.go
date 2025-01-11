package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/segmentio/kafka-go"
	_ "github.com/lib/pq"
)

type Message struct {
	RequestID string `json:"request_id"`
	UserID    int    `json:"user_id"`
	Username  string `json:"username"`
	URL       string `json:"url"`
}

func setupLogger() {
	logFileName := fmt.Sprintf("app-log-%s.log", time.Now().Format("2006-01-02"))
	logFile, err := os.OpenFile(logFileName, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Fatalf("Failed to open log file: %v", err)
	}
	log.SetOutput(logFile)
	log.SetFlags(log.Ldate | log.Ltime | log.Lshortfile)
}

func connectToDB(connStr string, dbChan chan<- *sql.DB, errChan chan<- error) {
	var db *sql.DB
	var err error

	for retries := 0; retries < 20; retries++ {
		db, err = sql.Open("postgres", connStr)
		if err != nil {
			log.Printf("Error opening database connection: %v", err)
			time.Sleep(5 * time.Second)
			continue
		}

		err = db.Ping()
		if err != nil {
			log.Printf("Error pinging database: %v", err)
			time.Sleep(5 * time.Second)
			continue
		}

		log.Println("Successfully connected to the database")
		dbChan <- db
		return
	}

	errChan <- fmt.Errorf("unable to connect to database after several attempts")
}

func connectToKafka(kafkaURL, topic string, partition int, kafkaChan chan<- *kafka.Reader, errChan chan<- error) {
	var reader *kafka.Reader
	var err error

	for retries := 0; retries < 20; retries++ {
		reader = kafka.NewReader(kafka.ReaderConfig{
			Brokers:   []string{kafkaURL},
			Topic:     topic,
			Partition: partition,
		})
		err = reader.SetOffset(kafka.LastOffset)
		if err == nil {
			log.Println("Successfully connected to Kafka")
			kafkaChan <- reader
			return
		}

		log.Printf("Error connecting to Kafka: %v", err)
		time.Sleep(5 * time.Second)
	}

	errChan <- fmt.Errorf("unable to connect to Kafka after several attempts")
}

func main() {
	setupLogger()

	kafkaURL := "kafka:9092"
	topic := "parsing_requests"
	partition := 0
	connStr := "user=postgres password=postgres host=postgres-service port=5432 sslmode=disable"

	dbChan := make(chan *sql.DB)
	kafkaChan := make(chan *kafka.Reader)
	errChan := make(chan error, 2)

	go connectToDB(connStr, dbChan, errChan)
	go connectToKafka(kafkaURL, topic, partition, kafkaChan, errChan)

	var db *sql.DB
	var kafkaReader *kafka.Reader
	select {
	case db = <-dbChan:
		defer db.Close()
		log.Println("Database connection established")
	case err := <-errChan:
		log.Fatalf("Error connecting to the database: %v", err)
	}

	select {
	case kafkaReader = <-kafkaChan:
		defer kafkaReader.Close()
		log.Println("Kafka connection established")
	case err := <-errChan:
		log.Fatalf("Error connecting to Kafka: %v", err)
	}

	for {
		msg, err := kafkaReader.ReadMessage(context.Background())
		if err != nil {
			log.Printf("Error reading message from Kafka: %v", err)
			time.Sleep(5 * time.Second)
			continue
		}

		var message Message
		if err := json.Unmarshal(msg.Value, &message); err != nil {
			log.Printf("Error unmarshaling message: %v", err)
			continue
		}

		_, err = db.Exec(`INSERT INTO form_orders (request_id, user_id, username, url) 
			VALUES ($1, $2, $3, $4)`,
			message.RequestID, message.UserID, message.Username, message.URL)
		if err != nil {
			log.Printf("Error inserting message into database: %v", err)
			continue
		}

		log.Printf("Inserted message into form_orders: %v", message)
	}
}
