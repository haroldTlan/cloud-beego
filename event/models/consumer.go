package models

import (
	"event/models/util"
	"github.com/astaxie/beego/orm"
	"github.com/crackcomm/nsqueue/consumer"

	"encoding/json"
	"fmt"
	"os"
	"time"
)

// setting topic
var (
	// websocket's channel
	EventTopic = New()
	// global map
	NsqEvents map[string]Setting
)

// handle nsq infos
func handle(msg *consumer.Message) {
	var data map[string]interface{}
	if err := json.Unmarshal(msg.Body, &data); err != nil {
		util.AddLog(err)
		return
	}
	result := eventJugde(data)

	// when result is nil or result is error, continue
	if _, ok := result.(error); ok || result == nil {
		fmt.Printf("%+v\n", data)
		msg.Success()
		return
	}

	// socket channel
	EventTopic.Publish(result)
	fmt.Printf("%+v\n", result)
	msg.Success()
}

// filter events
func eventJugde(values map[string]interface{}) (result interface{}) {
	// different events to do different operation
	switch values["event"].(string) {

	// Rozofs Client Setting
	case "cmd.client.add", "cmd.client.remove":
		count := values["count"].(float64)
		id := values["id"].(string)

		// update global data
		_count := RpcSetting("cmd.client.change", values)

		// update sql
		if err := ClientUpdate(values["ip"].(string), values["event"].(string), values["status"].(bool)); err != nil {
			util.AddLog(err)
			return nil
		}

		if count == _count {
			return NsqEvents[id]
		}

		return nil

	// Storage Setting, create raid, vol, fs then return results
	case "cmd.storage.build", "cmd.storage.remove":
		count := values["count"].(float64)
		id := values["id"].(string)
		event := values["event"].(string)

		// update global data
		_count := RpcSetting(event, values)

		// update sql
		if count == _count {
			if err := StorageUpdate(values["ip"].(string), NsqEvents[id].ErrCount, values["event"].(string)); err != nil {
				util.AddLog(err)
				return nil
			}
			return NsqEvents[id]
		}
		return nil

	default:
		// ordinary event setting
		machineId, err := Analyze(values["ip"].(string))
		if err != nil {
			return err
		}

		result = newEvent(values, machineId)
		if _, ok := result.(error); ok {
			util.AddLog(err)
			return nil
		}
		if err := RefreshOverViews(values["ip"].(string), values["event"].(string)); err != nil {
			util.AddLog(err)
		}
		return
	}

	return
}

// assert event
// return all key-value pairs
func newEvent(values map[string]interface{}, machineId string) interface{} {
	switch values["event"].(string) {

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

// checking whether the machine is being monitored
// return ip address or ip uuid?
func Analyze(ip string) (string, error) {
	o := orm.NewOrm()

	if exist := o.QueryTable(new(Machine)).Filter("ip", ip).Exist(); exist {
		return ip, nil
	}

	return "", fmt.Errorf("Machine is not being monitored")
}

// connect consumer 10 times
func RunConsumer(maxInFlight int, nsqdAddr string) {
	count := 10
	for {
		consumer.Register("CloudEvent", "consume86", maxInFlight, handle)
		err := consumer.Connect(nsqdAddr)
		if err == nil {
			util.AddLog(err)
			break
		}
		time.Sleep(time.Second * 10)
		count -= 1
		if count == 0 {
			util.AddLog(err)
			os.Exit(1)
		}
	}

	consumer.Start(true)
}
