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
	Event      string
	Count      int
	Error      int
	Success    int
	ErrorMsg   string
	SuccessMsg string
}

func init() {
	NsqEvents = make(map[string]Setting)
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

func handle(msg *consumer.Message) {
	var data map[string]interface{}
	if err := json.Unmarshal(msg.Body, &data); err != nil {
		AddLogtoChan(err)
		return
	}
	//fmt.Printf("%+v\n", string(msg.Body))
	result := eventJugde(data)

	eventTopic.Publish(result)
	fmt.Printf("%+v\n", result)
	msg.Success()
}

func eventJugde(values map[string]interface{}) interface{} {
	o := orm.NewOrm()
	switch values["event"].(string) {
	case "safety.created":
		return Safety{Event: values["event"].(string),
			Ip: values["ip"].(string)}

	case "info.warning", "info.normal":
		result := Warning{Event: values["event"].(string),
			Type:   values["type"].(string),
			Ip:     values["ip"].(string),
			Value:  values["value"].(float64),
			Status: values["status"].(string)}
		if result.Status == "true" {
			if err := RefreshInfoMail(result); err != nil {
				AddLogtoChan(err)
			}
		}
		return result

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
		result := newEvent(values, machineId)
		if value, ok := result.(error); ok {
			AddLogtoChan(value)
			return nil
		}
		if err := RefreshOverViews(values["ip"].(string), values["event"].(string)); err != nil {
			AddLogtoChan(err)
		}
		return result
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

	case "machine.created":
		InitSingleRemote(values["ip"].(string))
		return HeartBeat{Event: values["event"].(string),
			Ip:        values["ip"].(string),
			MachineId: machineId}
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
