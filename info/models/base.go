package models

import (
	_ "fmt"
	"github.com/astaxie/beego"
	"github.com/astaxie/beego/logs"
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
			if info.Dev == "storage" {
				s.Storages = append(s.Storages, dev)
			} else {
				s.Exports = append(s.Exports, dev)
			}
		}
		StatTopic.Publish(s)
		s.CheckStand()
		time.Sleep(time.Duration(interval) * time.Second)
	}
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
