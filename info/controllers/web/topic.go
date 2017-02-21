package controllers

import (
	"encoding/json"

	"github.com/astaxie/beego"
	"github.com/gorilla/websocket"
)

func Join(user string, ws *websocket.Conn) {
	subscribe <- Subscriber{Name: user, Conn: ws}
}

func Leave(user string) {
	unsubscribe <- user
}

type Subscriber struct {
	Name string
	Conn *websocket.Conn // Only for WebSocket users; otherwise nil.
}

var (
	// Channel for new join users.
	subscribe = make(chan Subscriber, 10)
	// Channel for exit users.
	unsubscribe = make(chan string, 10)
	// Send events here to Publish them.
	//Publish = make(chan CompareEvent, 10)
	Publish = make(chan interface{}, 10)
	// Map of subscribers.
	subscribers = make(map[string]*websocket.Conn)
)

// This function handles all incoming chan messages.
func chatroom() {
	for {
		select {
		case sub := <-subscribe:
			if !isUserExist(subscribers, sub.Name) {
				subscribers[sub.Name] = sub.Conn // Add user to the end of list.
			} else {
				beego.Info("User existed:", sub.Name, ";WebSocket:", sub.Conn != nil)
			}
		case event := <-Publish:
			// Notify.
			notifyWebSocket(event)

		case unsub := <-unsubscribe:
			ws, ok := subscribers[unsub]
			if ok {
				if ws != nil {
					//models.UpdateOnline(unsub,"false")
					ws.Close()
					beego.Error("WebSocket closed:", unsub)

				}
				delete(subscribers, unsub)
			}
		}
	}
}

// notifyWebSocket broadcasts messages to WebSocket users.
func notifyWebSocket(event CompareEvent) {
	data, err := json.Marshal(event)
	if err != nil {
		beego.Error("Fail to marshal event:", err)
		return
	}

	ws, ok := subscribers[event.Id]
	if ok {
		if ws != nil {
			if ws.WriteMessage(websocket.TextMessage, data) != nil {
				// User disconnected.
				unsubscribe <- event.Name
			}
		}
	} else {
		beego.Info("User existed:", event.Name, ";WebSocket:", ws != nil)
	}
}

func init() {
	go chatroom()
}

func isUserExist(subscribers map[string]*websocket.Conn, user string) bool {
	_, ok := subscribers[user]
	return ok
}
