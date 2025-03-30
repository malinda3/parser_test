package main

import (
	"bytes"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"os"
	"strings"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func main() {
	// Retrieve environment variables
	botToken := os.Getenv("BOT_TOKEN")
	if botToken == "" {
		log.Fatal("BOT_TOKEN is not set in the environment variables")
	}

	// Initialize the bot
	bot, err := tgbotapi.NewBotAPI(botToken)
	if err != nil {
		log.Panic(err)
	}

	bot.Debug = true
	log.Printf("Бот запущен: %s", bot.Self.UserName)

	// Retrieve the API URL for product details
	apiURL := os.Getenv("API_URL")
	if apiURL == "" {
		log.Println("Warning: API_URL is not set. Skipping API requests.")
	}

	u := tgbotapi.NewUpdate(0)
	u.Timeout = 60
	updates := bot.GetUpdatesChan(u)

	// Main loop to process updates
	for update := range updates {
		if update.Message == nil {
			continue
		}

		// Handle start command
		if update.Message.IsCommand() && update.Message.Command() == "start" {
			msg := tgbotapi.NewMessage(update.Message.Chat.ID, "Отправьте ссылку на товар")
			bot.Send(msg)
			continue
		}

		// Check if message contains a valid URL
		if !isURL(update.Message.Text) {
			continue
		}

		// If API_URL is not set, inform the user and skip the API call
		if apiURL == "" {
			msg := tgbotapi.NewMessage(update.Message.Chat.ID, "API_URL is not set. Skipping request.")
			bot.Send(msg)
			continue
		}

		// Log the API request
		log.Printf("Sending request to API URL: %s with URL: %s", apiURL, update.Message.Text)

		// Make the API request to fetch product details
		resp, err := http.Post(
			apiURL,
			"application/json",
			bytes.NewBufferString(`{"url":"`+update.Message.Text+`"}`),
		)
		if err != nil {
			log.Printf("Error making API request: %v", err)
			continue
		}
		defer resp.Body.Close()

		// Check for API response status
		if resp.StatusCode != http.StatusOK {
			log.Printf("API returned status: %v", resp.StatusCode)
			body, _ := io.ReadAll(resp.Body)
			log.Printf("Response body: %s", string(body))
			continue
		}

		// Parse API response
		var result struct {
			ProductInfo struct {
				Name  string `json:"name"`
				Price string `json:"price"`
			}
		}

		if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
			log.Printf("Error decoding response body: %v", err)
			continue
		}

		// Send the product info as a message
		msg := tgbotapi.NewMessage(update.Message.Chat.ID,
			"Название: "+result.ProductInfo.Name+"\nЦена: "+result.ProductInfo.Price)
		bot.Send(msg)
	}
}

// Helper function to check if the message is a URL
func isURL(text string) bool {
	return len(text) > 10 && (strings.HasPrefix(text, "http://") || strings.HasPrefix(text, "https://"))
}
