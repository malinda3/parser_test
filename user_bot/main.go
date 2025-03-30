
package main

import (
	"bytes"
	"encoding/json"
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

	for update := range updates {
		if update.Message == nil || !update.Message.IsCommand() && !isURL(update.Message.Text) {
			continue
		}

		if update.Message.IsCommand() && update.Message.Command() == "start" {
			msg := tgbotapi.NewMessage(update.Message.Chat.ID, "Отправьте ссылку на товар")
			bot.Send(msg)
			continue
		}

		resp, err := http.Post(
			os.Getenv("API_URL"),
			"application/json",
			bytes.NewBufferString(`{"url":"`+update.Message.Text+`"}`),
		)
		if err != nil {
			log.Printf("Ошибка API: %v", err)
			continue
		}
		defer resp.Body.Close()

		var result struct {
			ProductInfo struct {
				Name  string
				Price string
			}
		}
		json.NewDecoder(resp.Body).Decode(&result)

		msg := tgbotapi.NewMessage(update.Message.Chat.ID, 
			"Название: "+result.ProductInfo.Name+"\nЦена: "+result.ProductInfo.Price)
		bot.Send(msg)
	}
}

func isURL(text string) bool {
	return len(text) > 10 && (text[:7] == "http://" || text[:8] == "https://")
}