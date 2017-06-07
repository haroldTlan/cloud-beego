package controllers

import (
	"encoding/json"
	"event/models"
	"event/models/util"
	_ "fmt"

	"github.com/astaxie/beego"
	"github.com/gorilla/websocket"
	"net/http"
)

// WebSocketController handles WebSocket requests.
type WebSocketController struct {
	beego.Controller
}

func (this *WebSocketController) Join() {

	// Upgrade from http request to WebSocket.
	ws, err := websocket.Upgrade(this.Ctx.ResponseWriter, this.Ctx.Request, nil, 1024, 1024)
	if _, ok := err.(websocket.HandshakeError); ok {
		http.Error(this.Ctx.ResponseWriter, "Not a websocket handshake", 400)
		return
	} else if err != nil {
		util.AddLog(err, "Cannot setup WebSocket connection:")
		return
	}

	go func() {
		// handle nsq data
		util.AddLog("Logining")
		sub := models.EventTopic.Subscribe()
		defer models.EventTopic.Unsubscribe(sub)
		for {
			e := <-sub
			bytes, err := json.Marshal(e)
			if err != nil {
				util.AddLog(err)
			}
			err = ws.WriteMessage(websocket.TextMessage, bytes)
			if err != nil {
				util.AddLog(err)
				return
			}
		}
		defer ws.Close()
	}()

}
