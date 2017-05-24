package main

import (
	"flag"

	"encoding/json"
	"errors"
	"fmt"
	"github.com/astaxie/beego"
	"github.com/astaxie/beego/orm"
	"github.com/crackcomm/nsqueue/consumer"
	"os"
	"time"
)

var (
	nsq_ip      = beego.AppConfig.String("nsq") + ":" + beego.AppConfig.String("nsq_port")
	nsqdAddr    = flag.String("nsqd", nsq_ip, "nsqd http address")
	maxInFlight = flag.Int("max-in-flight", 200, "Maximum amount of messages in flight to consume")

	NsqEvents map[string]Setting
)

type Setting struct {
	Event    string
	Count    int
	ErrCount int
	Success  int
	ErrorMsg []ErrMsg
}
type ErrMsg struct {
	Ip  string
	Msg string
}

func init() {
	NsqEvents = make(map[string]Setting)
}

func handle(msg *consumer.Message) {
	var data map[string]interface{}
	if err := json.Unmarshal(msg.Body, &data); err != nil {
		AddLogtoChan(err)
		return
	}
	result := eventJugde(data)

	if result == nil {
		msg.Success()
		return
	}

	eventTopic.Publish(result)
	fmt.Printf("%+v\n", result)
	msg.Success()
}

func ClientSet(values map[string]interface{}) (count float64) {
	success, err := 0, 0
	errMsg := ""

	ip := values["ip"].(string)
	id := values["id"].(string)
	event := values["event"].(string)
	status := values["status"].(bool)
	detail := values["detail"].(string)

	if status {
		success = 1
	} else {
		err = 1
		errMsg = detail
	}
	if _, ok := NsqEvents[id]; ok {
		//when more then the first time
		_err := NsqEvents[id].ErrCount + err
		_success := NsqEvents[id].Success + success
		_count := NsqEvents[id].Count + 1
		_msg := NsqEvents[id].ErrorMsg
		if err == 1 {
			_msg = append(_msg, ErrMsg{Ip: ip, Msg: errMsg})
		}

		NsqEvents[id] = Setting{Count: _count, Event: event, ErrCount: _err, Success: _success, ErrorMsg: _msg}

	} else {
		//when failed, add error message
		msg := make([]ErrMsg, 0)
		if err == 1 {
			msg = []ErrMsg{ErrMsg{Ip: ip, Msg: errMsg}}
		}

		NsqEvents[id] = Setting{Count: 1, Event: event, ErrCount: err, Success: success, ErrorMsg: msg}
	}

	count = float64(NsqEvents[id].Count)
	return
}

func eventJugde(values map[string]interface{}) (result interface{}) {
	o := orm.NewOrm()
	switch values["event"].(string) {
	case "safety.created":
		return Safety{Event: values["event"].(string),
			Ip: values["ip"].(string)}

	case "info.warning", "info.normal":
		res := Warning{Event: values["event"].(string),
			Type:   values["type"].(string),
			Ip:     values["ip"].(string),
			Value:  values["value"].(float64),
			Status: values["status"].(string)}
		if res.Status == "true" {
			if err := RefreshInfoMail(res); err != nil {
				AddLogtoChan(err)
			}
		}
		return res

	case "cmd.client.add", "cmd.client.remove":
		//update global data
		count := values["count"].(float64)
		id := values["id"].(string)

		_count := ClientSet(values)
		temp1(values["ip"].(string), values["event"].(string), values["status"].(bool))
		fmt.Println("\n", count, "+", _count)
		fmt.Printf("%+v", NsqEvents[id])
		if count == _count {
			fmt.Printf("???%+v??", NsqEvents[id])
			return NsqEvents[id]
		}

		return nil

	case "cmd.storage.build", "cmd.storage.remove":
		temp2(values["ip"].(string), values["result"].(bool))
		var c Cluster
		var s Storage

		o.QueryTable("storage").Filter("ip", values["ip"].(string)).One(&s)
		o.QueryTable("cluster").Filter("uuid", s.Clusterid).One(&c)
		machineId := c.Uuid
		return Cmd{Event: values["event"].(string),
			Ip:        values["ip"].(string),
			Detail:    values["detail"].(string),
			Status:    values["result"].(bool),
			MachineId: machineId}

	default:
		machineId, err := analyze(values["ip"].(string))
		if err != nil {
			fmt.Println(err)
			return err
		}
		result = newEvent(values, machineId)
		if value, ok := result.(error); ok {
			AddLogtoChan(value)
			return nil
		}
		if err := RefreshOverViews(values["ip"].(string), values["event"].(string)); err != nil {
			AddLogtoChan(err)
		}
		return
	}
}

func newEvent(values map[string]interface{}, machineId string) interface{} {
	switch values["event"].(string) {
	case "cmd.client.add", "cmd.client.remove", "cmd.storage.build", "cmd.storage.remove":
		if values["event"].(string) == "cmd.client.add" || values["event"].(string) == "cmd.client.remove" {
			temp1(values["ip"].(string), values["event"].(string), values["result"].(bool))
		} else {
			temp2(values["ip"].(string), values["result"].(bool))
		}

		return Cmd{Event: values["event"].(string),
			Ip:        values["ip"].(string),
			Detail:    values["detail"].(string),
			Status:    values["result"].(bool),
			MachineId: machineId}
	case "ping.offline", "ping.online":
		return HeartBeat{Event: values["event"].(string),
			Ip:        values["ip"].(string),
			MachineId: machineId}

	case "fs.removed", "fs.created":
		return FsSystem{Event: values["event"].(string),
			Volume:    values["volume"].(string),
			Type:      values["type"].(string),
			MachineId: machineId,
			Ip:        values["ip"].(string)}

	case "disk.unplugged":
		return DiskUnplugged{Event: values["event"].(string),
			Uuid:      values["uuid"].(string),
			Location:  values["location"].(string),
			DevName:   values["dev_name"].(string),
			MachineId: machineId,
			Ip:        values["ip"].(string)}

	case "disk.plugged", "raid.created", "volume.created", "volume.removed", "raid.degraded", "raid.failed", "volume.failed", "volume.normal", "raid.normal":
		return DiskPlugged{Event: values["event"].(string),
			Uuid:      values["uuid"].(string),
			MachineId: machineId,
			Ip:        values["ip"].(string)}

	case "raid.removed":
		disks := values["raid_disks"].([]interface{})
		var ones []string
		for _, val := range disks {
			disk := val.(string)
			ones = append(ones, disk)
		}
		return RaidRemove{Event: values["event"].(string),
			Uuid:      values["uuid"].(string),
			RaidDisks: ones,
			MachineId: machineId,
			Ip:        values["ip"].(string)}
	}
	return nil
}

func analyze(machine string) (string, error) {
	if num, one, err := SelectMachine(machine); err == nil && num > 0 {
		return one.Uuid, nil
	}

	return "", errors.New("Machine is not being monitored")
}

func SettingEvent(event string) {

}

func temp1(ip, event string, status bool) {
	o := orm.NewOrm()

	var c Client
	o.QueryTable("client").Filter("ip", ip).All(&c) //TODO

	if event == "cmd.client.add" && status {
		c.Status = true
		if _, err := o.Update(&c); err != nil {
		}
	}

	if event == "cmd.client.remove" && status {
		if _, err := o.QueryTable(new(Client)).Filter("ip", ip).Delete(); err != nil {
		}
	}

}

func temp2(ip string, status bool) {
	o := orm.NewOrm()
	fmt.Println("status")
	var c Cluster
	var s Storage

	o.QueryTable("storage").Filter("ip", ip).One(&s)
	o.QueryTable("cluster").Filter("uuid", s.Clusterid).One(&c) //TODO

	c.Store = status

	o.Update(&c)
}

//connect consumer 10 times
func RunConsumer(maxInFlight int, nsqdAddr string) {
	count := 10
	for {
		consumer.Register("CloudEvent", "consume86", maxInFlight, handle)
		err := consumer.Connect(nsqdAddr)
		if err == nil {
			AddLogtoChan(err)
			break
		}
		time.Sleep(time.Second * 10)
		count -= 1
		if count == 0 {
			AddLogtoChan(err)
			os.Exit(1)
		}
	}

	consumer.Start(true)
}
