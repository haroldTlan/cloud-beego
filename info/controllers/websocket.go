package controllers

import (
	"encoding/json"
	//	"fmt"
	"github.com/astaxie/beego"
	"github.com/gorilla/websocket"
	"net/http"
	"time"
)

// WebSocketController handles WebSocket requests.
type WebSocketController struct {
	beego.Controller
}

type Event struct {
	Type      int // JOIN, LEAVE, MESSAGE
	User      string
	Timestamp int // Unix timestamp (secs)
	Content   string
}

func (this *WebSocketController) Join() {
	// Upgrade from http request to WebSocket.
	ws, err := websocket.Upgrade(this.Ctx.ResponseWriter, this.Ctx.Request, nil, 1024, 1024)
	if _, ok := err.(websocket.HandshakeError); ok {
		http.Error(this.Ctx.ResponseWriter, "Not a websocket handshake", 400)
		return
	} else if err != nil {
		beego.Error("Cannot setup WebSocket connection:", err)
		return
	}
	// handle ansible data
	Join("haha", ws)
	defer Leave("haha")

}

// broadcastWebSocket broadcasts messages to WebSocket users.
func broadcastWebSocket(event Event) {
	data, err := json.Marshal(event)
	if err != nil {
		beego.Error("Fail to marshal event:", err)
		return
	}
	ws, _ := subscribers[event.User]
	ws.WriteMessage(websocket.TextMessage, data)

	/*for sub := subscribers; sub != nil; sub = sub.Next() {
		// Immediately send event to WebSocket users.
		ws := sub.Value.(Subscriber).Conn
		if ws != nil {
			if ws.WriteMessage(websocket.TextMessage, data) != nil {
				// User disconnected.
				//			unsubscribe <- sub.Value.(Subscriber).Name
			}
		}
	}*/
}

func newEvent(ep int, user, msg string) Event {
	return Event{ep, user, int(time.Now().Unix()), msg}
}
