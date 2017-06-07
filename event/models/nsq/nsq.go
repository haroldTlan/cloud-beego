package nsq

import (
	"encoding/json"
	"fmt"
	"github.com/crackcomm/nsqueue/consumer"
	"os"
	"time"
)

//connect consumer 10 times
func RunConsumer(maxInFlight int, nsqdAddr string) {
	count := 10
	for {
		consumer.Register("CloudEvent", "consume86", maxInFlight, handle)
		err := consumer.Connect(nsqdAddr)
		if err == nil {
			//AddLogtoChan(err)
			break
		}
		time.Sleep(time.Second * 10)
		count -= 1
		if count == 0 {
			//AddLogtoChan(err)
			os.Exit(1)
		}
	}

	consumer.Start(true)
}

func handle(msg *consumer.Message) {
	var data map[string]interface{}
	if err := json.Unmarshal(msg.Body, &data); err != nil {
		//AddLogtoChan(err)
		return
	}
	/*result := eventJugde(data)

	if result == nil {
		msg.Success()
		return
	}

	eventTopic.Publish(result)*/
	fmt.Printf("%+v\n", data)
	msg.Success()
}
