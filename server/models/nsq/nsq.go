package nsq

import (
	"encoding/json"
	_ "fmt"
	"github.com/astaxie/beego"
	"github.com/crackcomm/nsqueue/producer"
)

type Ping struct {
	Event  string `json:"event"`
	Ip     string `json:"ip"`
	Status string `json:"status"`
}

type ClientNsq struct {
	Event  string `json:"event"`
	Ip     string `json:"ip"`
	Export string `json:"export"`
	Count  int    `json:"count"`
	Id     string `json:"id"`
}

type StorageNsq struct {
	Event string `json:"event"`
	Ip    string `json:"ip"`
	Loc   string `json:"loc"`
	Mount string `json:"mountpoint"`
	Level int    `json:"level"`
	Count int    `json:"count"`
	Id    string `json:"id"`
}

var (
	nsq_ip = beego.AppConfig.String("nsq") + ":" + beego.AppConfig.String("nsq_pub_port")
)

func NsqInit() {
	go func() {
		producer.Connect(nsq_ip)
	}()
}

func NewNsqRequest(topic string, msg interface{}) {
	producer.PublishJSONAsync(topic, msg, nil)
}

func NsqRequest(event, ip, status, topic string) {
	buffer := eventType(event, ip, status)
	producer.PublishAsync(topic, buffer, nil)
}

func eventType(event, ip, status string) []byte {
	var ping Ping

	ping.Event = event
	ping.Ip = ip
	ping.Status = status
	stringSlice, _ := json.Marshal(ping)
	buffer := []byte(stringSlice)
	return buffer
}
