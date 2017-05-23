package main

import (
	"fmt"
	"github.com/astaxie/beego/orm"
	"gopkg.in/yaml.v2"
	"io/ioutil"
	"os"
	"os/exec"
	"runtime"
	"strconv"
	"strings"
	"time"
)

type StatInfo struct {
	Exports  string `json:"exports"`
	Storages string `json:"storages"`
}

func RefreshOverViews(ip, event string) error {
	if err := InsertJournals(event, ip); err != nil {
		return err
	}

	_, one, err := SelectMachine(ip)
	if err != nil {
		return err
	}
	if err := MulAttention(ip, event); err != nil { //mul email sending
		return err
	}

	switch event {

	case "ping.offline":
		//RefreshStatRemove(one.Uuid)
		//	RefreshAnsible()
		if err := DeleteMachine(one.Uuid); err != nil {
			return err
		}

	case "ping.online":
		fmt.Println("online!!!!")
		time.Sleep(4 * time.Second)
		//RefreshStatAdd(one.Ip, one.Devtype)
		//	RefreshAnsible()
		/*if err := RefreshStores(one.Uuid); err != nil {
			return err
		}*/

	default:
		/*	if err := RefreshStores(one.Uuid); err != nil {
			return err
		}*/
	}

	return nil
}

func RefreshInfoMail(result Warning) error {
	o := orm.NewOrm()
	var machine, threshhold string

	switch result.Type {
	case "cpu":
		threshhold = "CPU"
	case "mem":
		threshhold = "内存"
	case "cache":
		threshhold = "缓存"
	case "sys":
		threshhold = "系统空间"
	case "fs":
		threshhold = "存储空间"
	default:
		threshhold = "未知"
	}

	if err := InsertJournals(result.Event, result.Ip); err != nil { //Insert emergency
		return err
	}

	ones := make([]Emergency, 0) //the lastest attention!
	if _, err := o.QueryTable("emergency").Filter("event", result.Event).Filter("status", 0).All(&ones); err != nil || len(ones) < 1 {
		return err
	}

	value := strconv.FormatFloat(result.Value, 'f', 2, 64)

	_, message := messageTransform(result.Event)
	if result.Ip == "All" {
		machine = "总览"
	} else {
		machine = result.Ip
	}
	RefreshMulAttention(ones[len(ones)-1].Uid, machine+message+" "+threshhold+value+"%")

	return nil
}

func MulAttention(ip, event string) error {
	o := orm.NewOrm()
	ones := make([]Emergency, 0)
	if _, err := o.QueryTable("emergency").Filter("event", event).Filter("status", 0).All(&ones); err != nil || len(ones) < 1 {
		return err
	}
	_, message := messageTransform(event)
	RefreshMulAttention(ones[len(ones)-1].Uid, ip+" "+message) //the lastest attention!
	return nil
}

func RefreshMulAttention(uid int, message string) {
	go func() {
		if _, err := SelectMulMails(uid, 1); err != nil { //look at the emergency status
			AddLogtoChan(err)
		}
		SendMails(message, 1)

		status, err := SelectMulMails(uid, 2)
		if err != nil {
			AddLogtoChan(err)
		}
		if status {
			return
		} else {
			SendMails(message, 2)
		}

		status, err = SelectMulMails(uid, 3)
		if err != nil {
			AddLogtoChan(err)
		}
		if status {
			return
		} else {
			SendMails(message, 3)
			return
		}
	}()
}

func RefreshStatRemove(uuid string) { //auto delete info.yml  monitoring
	o := orm.NewOrm()
	var one Machine
	if _, err := o.QueryTable("machine").Filter("uuid", uuid).All(&one); err != nil {
		fmt.Println(err)
	}
	ip := one.Ip

	path := "/root/code/yml/vars/info.yml"
	str := ReadConf(path)

	var stat StatInfo //yml struct
	var arrs []string
	yaml.Unmarshal([]byte(str), &stat)

	if one.Devtype == "export" {
		arr := strings.Split(stat.Exports, ",")
		for _, val := range arr {
			if val == ip {
				continue
			}
			arrs = append(arrs, val)
		}
		stat.Exports = strings.Join(arrs, ",")
	} else {
		arr := strings.Split(stat.Storages, ",")
		for _, val := range arr {
			if val == ip {
				continue
			}
			arrs = append(arrs, val)
		}
		stat.Storages = strings.Join(arrs, ",")
	}
	down, _ := yaml.Marshal(&stat)
	WriteConf(path, fmt.Sprintf("---\n%s\n", string(down)))
}

func RefreshStatAdd(ip, devtype string) { //auto add info.yml
	path := "/root/code/yml/vars/info.yml"

	str := ReadConf(path)
	var stat StatInfo
	yaml.Unmarshal([]byte(str), &stat)
	if devtype == "export" && !strings.Contains(stat.Exports, ip) {
		stat.Exports = stat.Exports + "," + ip
	} else if devtype == "storage" && !strings.Contains(stat.Storages, ip) {
		stat.Storages = stat.Storages + "," + ip
	}

	down, _ := yaml.Marshal(&stat)
	WriteConf(path, fmt.Sprintf("---\n%s\n", string(down)))
}

func SendMails(message string, level int) {
	o := orm.NewOrm()
	var adds []Mail
	mails := make([]string, 0)
	if _, err := o.QueryTable("mail").Filter("level", level).All(&adds); err != nil {
		AddLogtoChan(err)
	}
	for _, val := range adds {
		mails = append(mails, val.Address)
	}
	MailSending(mails, message)
}

func RefreshAnsible() {
	for i := 0; i < 5; i++ {
		fmt.Println(i)
		if _, err := exec.Command("python", "/etc/ansible/info/device.py").Output(); err != nil {
			AddLogtoChan(err)
		}
	}
}

func AddLogtoChan(err error) {
	var message string
	var log Log
	if err == nil {
		message = fmt.Sprintf("[EVENT]event success")
		log = Log{Level: "INFO", Message: message}
	} else {
		pc, fn, line, _ := runtime.Caller(1)
		message = fmt.Sprintf("[EVENT][%s %s:%d] %s", runtime.FuncForPC(pc).Name(), fn, line, err)
		log = Log{Level: "ERROR", Message: message}
	}

	ChanLogEvent <- log
	return
}

func ReadConf(path string) string {
	fi, err := os.Open(path)
	if err != nil {
		panic(err)
	}
	defer fi.Close()
	fd, err := ioutil.ReadAll(fi)
	return string(fd)
}

func WriteConf(path string, str string) {
	yaml := []byte(str)

	fi, err := os.Open(path)
	if err != nil {
		panic(err)
	}
	defer fi.Close()
	err = ioutil.WriteFile(path, yaml, 0666)
	if err != nil {
		panic(err)
	}

}
