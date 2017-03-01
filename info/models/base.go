package models

import (
	"encoding/json"
	_ "fmt"
	"github.com/astaxie/beego"
	"github.com/astaxie/beego/logs"
	"io/ioutil"
	"math"
	"os"
	"os/exec"
	"runtime"
	"time"
)

var StatTopic = New() //set topic

func init() {
	Ansible()
	//InfoStat()
}

//get statistics from local
func InfoStat() {
	go func() {
		for {
			interval, err := beego.AppConfig.Int("interval")
			if err != nil {
				AddLog(err)
			}
			str := readConf("static/static")
			static := make([]Results, 0)
			if err := json.Unmarshal([]byte(str), &static); err != nil {
				AddLog(err)
			}

			var s Statistics
			s.Exports = make([]Device, 0)
			s.Storages = make([]Device, 0)

			for _, val := range static {
				if len(val.Result) > 0 {
					var dev Device
					info := microAdjust(&val.Result[len(val.Result)-1]) //get the lastest one statistics

					dev.Info = append(dev.Info, info)
					dev.Ip = val.Ip
					if val.Type == "storeInfo" {
						s.Storages = append(s.Storages, dev)
					} else {
						s.Exports = append(s.Exports, dev)
					}
				}
			}
			StatTopic.Publish(s)
			s.CheckStand()
			time.Sleep(time.Duration(interval) * time.Second)
		}
	}()
}

//Running ansible to get Statistics
func Ansible() {
	go func() {
		for {
			ansibleFrequency, err := beego.AppConfig.Int("ansible")
			if err != nil {
				AddLog(err)
			}
			if _, err := exec.Command("python", "models/device.py").Output(); err != nil {
				AddLog(err)
			}
			time.Sleep(time.Duration(ansibleFrequency) * time.Second)
		}
	}()
}

//set some value from KB to MB or ...
func microAdjust(devInfo *StoreView) StoreView {
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

//keep the places of decimal you want
func Round(f float64, n int) float64 {
	pow10_n := math.Pow10(n)

	return math.Trunc((f+0.5/pow10_n)*pow10_n) / pow10_n
}

//read static
func readConf(path string) string {
	fi, err := os.Open(path)
	if err != nil {
		panic(err)
		AddLog(err)
	}
	defer fi.Close()
	fd, err := ioutil.ReadAll(fi)
	if err != nil {
		AddLog(err)
	}

	return string(fd)
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
