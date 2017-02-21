package controllers

import (
	"encoding/json"
	"fmt"
	"github.com/astaxie/beego"
	//"github.com/astaxie/beego/config"
	"github.com/gorilla/websocket"
)

var (
	// Channel for new join users.
	subscribe = make(chan Subscriber, 10)
	// Channel for exit users.
	unsubscribe = make(chan string, 10)
	// Send events here to Publish them.
	Publish = make(chan interface{}, 10)
	// Map of subscribers.
	subscribers = make(map[string]*websocket.Conn)
)

func Push(d interface{}) {
	Publish <- d
}

func Join(user string, ws *websocket.Conn) {
	a, b := beego.AppConfig.Int("ansible")
	fmt.Println("name ", a, b)
	//fmt.Println("config path ", beego.AppConfigPath)
	event := newEvent(2, user, "haha")
	data, err := json.Marshal(event)
	if err != nil {
		beego.Error("Fail to marshal event:", err)
		return
	}
	ws.WriteMessage(websocket.TextMessage, data)

	subscribe <- Subscriber{Name: user, Conn: ws}

}

func Leave(user string) {
	unsubscribe <- user
}

type Subscriber struct {
	Name string
	Conn *websocket.Conn // Only for WebSocket users; otherwise nil.
}

func statTopic() {
	for {
		select {
		case data := <-Publish:
			fmt.Println(data)

		case sub := <-subscribe:
			fmt.Println("sub")
			fmt.Println(sub)
		case unsub := <-unsubscribe:
			ws, ok := subscribers[unsub]
			if ok {
				if ws != nil {

					ws.Close()
					beego.Error("WebSocket closed:", unsub)
				}
				delete(subscribers, unsub)
			}
		}
	}
}

/*
func chatroom() {
	for {
		select {
		case sub := <-subscribe:
			fmt.Println("sub")
			//	subscribers[sub.Name] = sub.Conn // Add user to the end of list.
			beego.Info("User existed:", sub.Name, ";WebSocket:", sub.Conn != nil)
		case event := <-Publish:
			// Notify.
			fmt.Println("event")
		case unsub := <-unsubscribe:
			ws, ok := subscribers[unsub]
			if ok {
				if ws != nil {
					ws.Close()
					beego.Error("WebSocket closed:", unsub)

				}
				delete(subscribers, unsub)
			}
		}
	}
}*/

func init() {
	go statTopic()
}
