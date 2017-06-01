package models

import (
	_ "fmt"
	"github.com/astaxie/beego"
	"github.com/astaxie/beego/logs"
	"github.com/astaxie/beego/orm"

	"encoding/json"
	//"fmt"
	"math"
	"runtime"
	"time"
)

var StatTopic = New() //set topic

//get infos from nsq
func InfoStat() {
	for {
		interval, err := beego.AppConfig.Int("interval")
		if err != nil {
			AddLog(err)
		}

		var s Statistics
		s.Exports = make([]Device, 0)
		s.Storages = make([]Device, 0)
		for _, info := range NsqInfos { //NsqInfos is global variable
			var dev Device
			dev.Info = append(dev.Info, info)
			dev.Ip = info.Ip

			//writing in local
			if info.Dev == "storage" {
				if sameDevice(dev.Ip) {
					info.Dev = "export"
					s.Exports = append(s.Exports, Device{Info: []StoreView{info}, Ip: info.Ip})
				}
				s.Storages = append(s.Storages, dev)
			} else {
				s.Exports = append(s.Exports, dev)
			}
		}
		//fmt.Printf("%+v", s.Exports)

		StatTopic.Publish(s)
		s.CheckStand()
		time.Sleep(time.Duration(interval) * time.Second)
	}
}

func (d Drawing) drawSetting(i StoreView) {
	if i.Dev == "export" {
		return
	}
	d.Ip = i.Ip
	d.Dev = i.Dev
	/*d.Dfs = i.Dfs
	d.Cpu = i.Cpu
	d.Mem = i.Mem
	d.MemT = i.MemT
	d.Temp = i.Temp*/
	d.Write = i.Write
	d.Read = i.Read
	d.TimeStamp = i.TimeStamp
	d.CacheT = i.CacheT
	d.CacheU = i.CacheU
	d.W_Vol = i.W_Vol
	d.R_Vol = i.R_Vol

	for _, i := range i.Dfs {
		if i.Name == "tmp" {
			d.Tmp = i.Used_per
		} else if i.Name == "system" {
			d.System = i.Used_per
		} else if i.Name == "weed_cpu" {
			d.WeedCpu = i.Used_per
		} else if i.Name == "weed_mem" {
			d.WeedMem = i.Used_per
		} else if i.Name == "var" {
			d.Var = i.Used_per
		}

	}

	first, _ := json.Marshal(d)
	//second, _ := json.Marshal("\t\n\n")
	//first = append(first, second[1:5]...)
	path := beego.AppConfig.String("drawing")
	WriteConf(path, first)
}

func sameDevice(ip string) (exist bool) {
	o := orm.NewOrm()

	exist = o.QueryTable(new(Machine)).Filter("ip", ip).Filter("devtype", "export").Exist()
	return
}

//set some value from KB to MB or ... Not Used
func microAdjust(devInfo *StoreView) StoreView {
	devInfo.W_Vol = Round(devInfo.W_Vol/1024, 2)
	devInfo.R_Vol = Round(devInfo.R_Vol/1024, 2)
	for i, _ := range devInfo.Dfs {
		if devInfo.Dfs[i].Name == "weed_mem" || devInfo.Dfs[i].Name == "weed_cpu" {
			continue
		} else {
			devInfo.Dfs[i].Total = Round(devInfo.Dfs[i].Total/1024.0/1024.0, 2)
			devInfo.Dfs[i].Available = Round(devInfo.Dfs[i].Available/1024.0/1024.0, 2)
		}
	}
	return *devInfo
}

//keep the places of decimal you want  Not Used
func Round(f float64, n int) float64 {
	pow10_n := math.Pow10(n)
	return math.Trunc((f+0.5/pow10_n)*pow10_n) / pow10_n
}

//logs
func AddLog(err interface{}, v ...interface{}) {
	if _, ok := err.(error); ok {
		pc, _, line, _ := runtime.Caller(1)
		logs.Error("[Info] ", runtime.FuncForPC(pc).Name(), line, v, err)
	} else {
		logs.Info("[Info] ", err)
	}
}
