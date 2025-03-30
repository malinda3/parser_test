package main

import (
	"bytes"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"os"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func main() {
	bot, err := tgbotapi.NewBotAPI(os.Getenv("BOT_TOKEN"))
	if err != nil {
		log.Panic(err)
	}

	bot.Debug = true
	log.Printf("Бот запущен: %s", bot.Self.UserName)

	u := tgbotapi.NewUpdate(0)
	u.Timeout = 60

	updates := bot.GetUpdatesChan(u)

	// Check if API_URL is set
	apiURL := os.Getenv("API_URL")
	if apiURL == "" {
		// Log a warning message and skip API requests
		log.Println("Warning: API_URL is not set. API requests will be skipped.")
	}

	for update := range updates {
		if update.Message == nil || !update.Message.IsCommand() && !isURL(update.Message.Text) {
			continue
		}

		if update.Message.IsCommand() && update.Message.Command() == "start" {
			msg := tgbotapi.NewMessage(update.Message.Chat.ID, "Отправьте ссылку на товар")
			bot.Send(msg)
			continue
		}

		// If API_URL is not set, skip the API request
		if apiURL == "" {
			msg := tgbotapi.NewMessage(update.Message.Chat.ID, "API_URL is not set. Skipping request.")
			bot.Send(msg)
			continue
		}

		log.Printf("Sending request to URL: %s", apiURL)
		log.Printf("Request payload: %s", `{"url":"`+update.Message.Text+`"}`)

		resp, err := http.Post(
			apiURL,
			"application/json",
			bytes.NewBufferString(`{"url":"`+update.Message.Text+`"}`),
		)
		if err != nil {
			log.Printf("Ошибка API: %v", err)
			continue
		}
		defer resp.Body.Close()

		// Log response status and body for debugging
		if resp.StatusCode != http.StatusOK {
			log.Printf("API returned status: %v", resp.StatusCode)
			body, _ := io.ReadAll(resp.Body)
			log.Printf("Response body: %s", string(body))
			continue
		}

		var result struct {
			ProductInfo struct {
				Name  string
				Price string
			}
		}
		if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
			log.Printf("Error decoding response body: %v", err)
			continue
		}

		msg := tgbotapi.NewMessage(update.Message.Chat.ID,
			"Название: "+result.ProductInfo.Name+"\nЦена: "+result.ProductInfo.Price)
		bot.Send(msg)
	}
}

func isURL(text string) bool {
	return len(text) > 10 && (text[:7] == "http://" || text[:8] == "https://")
}
