package nsq

import (
	"encoding/json"
	"fmt"
	"github.com/astaxie/beego"
	"github.com/crackcomm/nsqueue/producer"
)

type Ping struct {
	Event  string `json:"event"`
	Ip     string `json:"ip"`
	Status string `json:"status"`
}

var (
	nsq_ip = beego.AppConfig.String("nsq") + ":" + beego.AppConfig.String("nsq_pub_port")
)

func NsqInit() {
	go func() {
		producer.Connect(nsq_ip)
	}()
}

func NsqRequest(event, ip, status, topic string) {
	buffer := eventType(event, ip, status)
	fmt.Printf("\n\n\n%+v\n\n\n", string(buffer))
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
