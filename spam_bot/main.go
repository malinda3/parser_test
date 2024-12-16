package main

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"time"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
	_ "github.com/lib/pq"
)

const (
	dbHost     = "postgres"
	dbPort     = "5432"
	dbName     = "orders"
	dbUser     = "postgres"
	dbPassword = "postgres"
)

func main() {
	// Создаем подключение к базе данных
	connStr := fmt.Sprintf("host=%s port=%s dbname=%s user=%s password=%s sslmode=disable",
		dbHost, dbPort, dbName, dbUser, dbPassword)
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
	botToken := "6316465274:AAF9Tm5rAVwTTVaoO4SjgqqCTdluM1o-IWI"
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

	// Обработка входящих сообщений
	for update := range updates {
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
	}
}

// getUniqueUsers - функция для получения уникальных пользователей из базы данных
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
