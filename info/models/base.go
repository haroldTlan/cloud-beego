package models

import (
	"encoding/json"
	"fmt"
	"github.com/astaxie/beego"
	"io/ioutil"
	"os"
	"os/exec"
	"time"

	"math"
)

//get data from local
func InfoStat() {
	go func() {
		str := readConf("/root/go/src/beego_info/static/static")
		static := make([]Results, 0)
		if err := json.Unmarshal([]byte(str), &static); err != nil {
			beego.Error(err)
		}

		var s Statistics
		for _, val := range static {
			var dev Device
			dev.Ip = val.Ip
			info := microAdjust(&val.Result[len(val.Result)-1]) //get the lastest one statistics
			dev.Info = append(dev.Info, info)
			if val.Type == "storeInfo" {
				s.Storages = append(s.Storages, dev)
			} else {
				s.Exports = append(s.Exports, dev)
			}
		}
		fmt.Println(s)
	}()
}

func Ansible() {
	go func() {
		for {
			ansibleFrequency, err := beego.AppConfig.Int("ansible")
			if err != nil {
				beego.Error(err)
			}
			if _, err := exec.Command("python", "models/device.py").Output(); err != nil {
				beego.Error(err)
			}
			time.Sleep(time.Duration(ansibleFrequency) * time.Second)
		}
	}()
}

func microAdjust(devInfo *StoreView) StoreView {
	for i, _ := range devInfo.Dfs {
		devInfo.Dfs[i].Total = Round(devInfo.Dfs[i].Total/1024.0/1024.0, 2)
		devInfo.Dfs[i].Available = Round(devInfo.Dfs[i].Available/1024.0/1024.0, 2)
	}

	return *devInfo
}

func Round(f float64, n int) float64 {
	pow10_n := math.Pow10(n)
	return math.Trunc((f+0.5/pow10_n)*pow10_n) / pow10_n
}

func readConf(path string) string {
	fi, err := os.Open(path)
	if err != nil {
		beego.Error(err)
	}
	defer fi.Close()
	fd, err := ioutil.ReadAll(fi)
	if err != nil {
		beego.Error(err)
	}
	return string(fd)
}
