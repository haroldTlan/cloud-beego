package models

import (
	"encoding/json"
	"errors"
	_ "fmt"
	"github.com/astaxie/beego/orm"
	"github.com/crackcomm/nsqueue/consumer"
	"os"
	"sync"
	"time"
)

var (
	infos map[string]StoreView
	l     sync.RWMutex
)

func init() {
	infos = make(map[string]StoreView)
}

func handle(msg *consumer.Message) {

	data := make([]StoreView, 0)
	if err := json.Unmarshal(msg.Body, &data); err != nil { //get infos from machines
		AddLog(err)
		msg.Fail()
		return
	}
	if len(data) > 0 {
		for _, val := range data {
			err := selectMachines(val.Ip)
			if err != nil {
				continue
			}
			if val.Ip == "" || val.Ip == "unknow" {
				continue
			} else {
				InfoTest(&val, val.Ip)
			}
		}
	}
	msg.Success() //TODO means
}

func InfoTest(data *StoreView, ip string) {
	l.RLock()
	if _, ok := infos[ip]; ok {
		l.RUnlock()
		l.Lock()
		for i, _ := range data.Dfs {
			if data.Dfs[i].Name == "weed_mem" || data.Dfs[i].Name == "weed_cpu" {
				continue
			} else {
				data.Dfs[i].Total = Round(data.Dfs[i].Total/1024.0/1024.0, 2)
				data.Dfs[i].Available = Round(data.Dfs[i].Available/1024.0/1024.0, 2)
			}
		}
		infos[ip] = *data
		l.Unlock()
	} else {
		l.RUnlock()
		infos[ip] = StoreView{Dev: data.Dev} //TODO init
	}
}

func selectMachines(ip string) error {
	o := orm.NewOrm()
	exist := o.QueryTable(new(Machine)).Filter("status", 1).Filter("ip", ip).Exist()
	if !exist {
		return errors.New("UnMonitoring")
	}
	return nil
}

func ClearInfos() {
	for {
		o := orm.NewOrm()
		for _, val := range infos {
			exist := o.QueryTable(new(Machine)).Filter("status", true).Filter("ip", val.Ip).Exist()
			if !exist {
				delete(infos, val.Ip)
			}
		}
		time.Sleep(time.Second * 10)

	}
}

func RunConsumer(maxInFlight int, nsqdAddr string) {
	count := 10
	for {
		consumer.Register("CloudInfo", "consume", maxInFlight, handle)
		err := consumer.Connect(nsqdAddr)
		if err == nil {
			AddLog(err)
			break
		}
		time.Sleep(time.Second * 10)
		count -= 1
		if count == 0 {
			AddLog(err)
			os.Exit(1)
		}
	}

	consumer.Start(true)
}
