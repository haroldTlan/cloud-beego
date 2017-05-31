package models

import (
	"encoding/json"
	"errors"
	"github.com/astaxie/beego"
	"github.com/astaxie/beego/orm"
	"github.com/crackcomm/nsqueue/consumer"
	"os"
	"sync"
	"time"

	"fmt"
)

var (
	NsqInfos map[string]StoreView //global variable
	l        sync.RWMutex         //lock
)

func init() {
	NsqInfos = make(map[string]StoreView)
}

//Handle infos from nsq consumer
func handle(msg *consumer.Message) {
	data := make([]StoreView, 0)
	if err := json.Unmarshal(msg.Body, &data); err != nil { //get infos from machines
		fmt.Println((string(msg.Body)))
		AddLog(err)
		msg.Fail()
		return
	}

	if len(data) > 0 {
		for _, val := range data {
			//avoid array gate null
			if val.Gate == nil {
				val.Gate = make([]Gates, 0)
			} else if val.Fs == nil {
				val.Fs = make([]Df, 0)
			}

			err := selectMachines(val.Ip)
			if err != nil {
				continue
			}
			if val.Ip == "" || val.Ip == "unknow" {
				continue
			} else {
				InfoTest(&val, val.Ip)
			}
			if val.Dev == "storage" {
				AddRest(val.Ip, val.Rest) //update rest
			}
		}
	}
	msg.Success() //TODO means
}

//Write infos in global varible
func InfoTest(data *StoreView, ip string) {
	l.RLock()
	if _, ok := NsqInfos[ip]; ok {
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
		for i, _ := range data.Fs {
			data.Fs[i].Total = Round(data.Fs[i].Total/1024.0/1024.0, 2)
			data.Fs[i].Available = Round(data.Fs[i].Available/1024.0/1024.0, 2)
		}

		NsqInfos[ip] = *data
		l.Unlock()
	} else {
		l.RUnlock()
		NsqInfos[ip] = *data
		//	NsqInfos[ip] = StoreView{Dev: data.Dev} //TODO init
	}
}

//Select infos whether is being monitored
func selectMachines(ip string) error {
	o := orm.NewOrm()
	exist := o.QueryTable(new(Machine)).Filter("status", 1).Filter("ip", ip).Exist()
	if !exist {
		return errors.New("UnMonitoring")
	}
	return nil
}

//clear global when machine not being monitored
func ClearInfos() {
	for {
		o := orm.NewOrm()
		for _, val := range NsqInfos {
			exist := o.QueryTable(new(Machine)).Filter("status", true).Filter("ip", val.Ip).Exist()
			if !exist {
				delete(NsqInfos, val.Ip)
			}

			checkTime, _ := beego.AppConfig.Int("checkpyc")
			val.Online += -1
			//when online is too low, mail
			if val.Online == checkTime {
				Mailing(val.Ip + " info.pyc not running")
			}
		}
		time.Sleep(time.Second * 10)
	}
}

//connect consumer 10 times
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
