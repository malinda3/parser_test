package main

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/joho/godotenv"
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
	_ "github.com/lib/pq"
)

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Fatalf("Ошибка загрузки .env файла: %v", err)
	}
	dbHost := os.Getenv("DB_HOST")
	dbPort := os.Getenv("DB_PORT")
	dbUser := os.Getenv("DB_USER")
	dbPassword := os.Getenv("DB_PASSWORD")
	

	// Создаем подключение к базе данных
	connStr := fmt.Sprintf("host=%s port=%s user=%s password=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword)
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		log.Fatalf("Ошибка подключения к базе данных: %v", err)
	}
	defer db.Close()

	// Проверка подключения
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := db.PingContext(ctx); err != nil {
		log.Fatalf("Ошибка проверки соединения с базой данных: %v", err)
	}

	// Создаем Telegram-бота
	botToken := os.Getenv("TELEGRAM_TOKEN")
	bot, err := tgbotapi.NewBotAPI(botToken)
	if err != nil {
		log.Fatalf("Ошибка создания Telegram-бота: %v", err)
	}

	bot.Debug = true // Логирование запросов бота
	log.Printf("Авторизован под аккаунтом %s", bot.Self.UserName)

	// Создаем обновления (polling)
	u := tgbotapi.NewUpdate(0)
	u.Timeout = 60

	updates := bot.GetUpdatesChan(u)
	
	for update := range updates {
		if isAllowed(update.Message.From.ID) {
		if update.Message != nil && update.Message.IsCommand() {
			switch update.Message.Command() {
			case "start":
				response := getUniqueUsers(db)
				msg := tgbotapi.NewMessage(update.Message.Chat.ID, response)
				bot.Send(msg)
			default:
				msg := tgbotapi.NewMessage(update.Message.Chat.ID, "Неизвестная команда.")
				bot.Send(msg)
			}
		}
	} else {
		msg := tgbotapi.NewMessage(update.Message.Chat.ID, "Неизвестная команда.")
		bot.Send(msg)
	}
}
}


func isAllowed(userID int64) bool {
	var allowedIDs = []int64{452009220, 5876847299} 
	fmt.Printf("ID: %d", userID)
	for _, id := range allowedIDs {
		if id == userID {
			return true
		}
	}
	return false
}

// getUniqueUsers - функция для получения уникальных пользователей из бд, делает запрос и работает с полученными данными
func getUniqueUsers(db *sql.DB) string {
	query := `
		SELECT DISTINCT user_id, username
		FROM public.form_orders
		WHERE username IS NOT NULL
	`

	rows, err := db.Query(query)
	if err != nil {
		log.Printf("Ошибка выполнения запроса: %v", err)
		return "Ошибка выполнения запроса к базе данных."
	}
	defer rows.Close()

	var users []string
	for rows.Next() {
		var userID int
		var username string
		if err := rows.Scan(&userID, &username); err != nil {
			log.Printf("Ошибка обработки строки результата: %v", err)
			return "Ошибка обработки данных из базы."
		}
		users = append(users, fmt.Sprintf("UserID: %d, Username: %s\n", userID, username))
	}

	if len(users) == 0 {
		return "Нет данных для отображения."
	}

	return "Уникальные пользователи:\n" + fmt.Sprintf("%s", users)
}
