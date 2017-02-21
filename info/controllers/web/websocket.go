package controllers

import (
	"fmt"
	"net/http"

	"github.com/astaxie/beego"
	"github.com/gorilla/websocket"
	"strings"
)

// WebSocketController handles WebSocket requests.
type WebSocketController struct {
	beego.Controller
}

// Join method handles WebSocket requests for WebSocketController.
func (this *WebSocketController) Join() {
	//uname := this.GetString("uname")
	uname := "aaaaa"
	if len(uname) == 0 {
		this.Redirect("/", 302)
		return
	}
	/*if strings.Contains(uname,".")||strings.Contains(uname,"@"){
		uname = models.QueryAccountWithEmail(uname)
	}*/
	// Upgrade from http request to WebSocket.
	ws, err := websocket.Upgrade(this.Ctx.ResponseWriter, this.Ctx.Request, nil, 1024, 1024)
	if _, ok := err.(websocket.HandshakeError); ok {
		http.Error(this.Ctx.ResponseWriter, "Not a websocket handshake", 400)
		return
	} else if err != nil {
		beego.Error("Cannot setup WebSocket connection:", err)
		return
	}

	_, token := models.QueryLoginToken(uname)
	//Publish <- NewTestEvent(uname,token)
	Publish <- uname
	if isUserExist(subscribers, uname) {
		fmt.Println(subscribers)

		fmt.Println(subscribers)

	}
	Join(uname, ws)
	defer Leave(uname)

	//Publish <- NewTestEvent(uname+"join")
	fmt.Println("ok", uname)
	fmt.Println(subscribers)
	// Message receive loop.
	for {
		_, _, err := ws.ReadMessage()
		if err != nil {
			return
		}
	}
	// Join
	//subscribers[uname].Close()

}
