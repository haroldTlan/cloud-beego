package main

import (
	"errors"
	"fmt"
	"github.com/astaxie/beego"
	"github.com/astaxie/beego/orm"
	_ "github.com/go-sql-driver/mysql"
	"time"
)

var (
	unused       = make(map[string]string)
	registerIp   = beego.AppConfig.String("registerDB")
	registerPort = beego.AppConfig.String("registerPort")
)

func Initdb() {
	orm.RegisterDriver("mysql", orm.DRMySQL)
	orm.RegisterDataBase("default", "mysql", "root:passwd@tcp("+registerIp+":"+registerPort+")/speediodb?charset=utf8&loc=Local", 50, 50)
	orm.RegisterModel(new(Storage), new(Cluster), new(Client), new(Fs), new(Journals), new(Machine), new(Disks), new(Raids), new(Volumes), new(Initiators), new(Emergency), new(Mail), new(Journal))
}

// DeleteMachine deletes Machine by Id and returns error if
// the record to be deleted doesn't exist
func DeleteMachine(uuid string) (err error) {
	o := orm.NewOrm()
	// ascertain id exists in the database
	if exist := o.QueryTable("machine").Filter("uuid", uuid).Exist(); exist {
		if _, err = o.QueryTable(new(Disks)).Filter("machineid", uuid).Delete(); err != nil {
			return
		}
		if _, err = o.QueryTable(new(Raids)).Filter("machineid", uuid).Delete(); err != nil {
			return
		}
		if _, err = o.QueryTable(new(Volumes)).Filter("machineid", uuid).Delete(); err != nil {
			return
		}
		if _, err = o.QueryTable(new(Initiators)).Filter("machineid", uuid).Delete(); err != nil {
			return
		}
		if _, err = o.QueryTable(new(Fs)).Filter("machineid", uuid).Delete(); err != nil {
			return
		}
		if _, err = o.QueryTable(new(Journals)).Filter("machineid", uuid).Delete(); err != nil {
			return
		}
	} else {
		err = errors.New("uuid not exits")
		return
	}
	return nil
}

func SelectMachine(ip string) (int64, Machine, error) {
	o := orm.NewOrm()
	var one Machine
	num, err := o.QueryTable("machine").Filter("ip", ip).All(&one)
	if err != nil {
		AddLogtoChan(err)
		fmt.Println(o.Driver().Name())
		return 0, one, err
	}
	return num, one, nil
}

func SelectMulMails(uid int, level int) (bool, error) {
	o := orm.NewOrm()
	var one Mail
	var two Emergency
	if _, err := o.QueryTable("mail").Filter("level", level).All(&one); err != nil {
		AddLogtoChan(err)
		return two.Status, err
	}
	time.Sleep(time.Duration(one.Ttl) * time.Second)

	if _, err := o.QueryTable("emergency").Filter("uid", uid).All(&two); err != nil {
		AddLogtoChan(err)
		return two.Status, err
	}
	return two.Status, nil
}

func InsertJournals(event, machine string) error {
	o := orm.NewOrm()
	var one Emergency
	switch event {
	case "ping.offline", "disk.unplugged", "raid.degraded", "volume.failed", "raid.failed", "info.warning":
		one.Level = "warning"
		one.Status = false
	default:
		one.Level = "info"
		one.Status = true
	}
	message, chinese_message := messageTransform(event)

	one.Message = message
	one.ChineseMessage = "设备" + " " + machine + " " + chinese_message
	one.Event = event
	one.Ip = machine
	one.Created_at = time.Now()
	one.Updated_at = time.Now()
	if _, err := o.Insert(&one); err != nil {
		AddLogtoChan(err)
		return err
	}

	return nil
}

func messageTransform(event string) (string, string) {
	switch event {
	case "ping.offline":
		message := "offline"
		chinese_message := "设备掉线"
		return message, chinese_message
	case "ping.online":
		message := "online"
		chinese_message := "设备上线"
		return message, chinese_message
	case "disk.unplugged":
		message := "disk unplugged"
		chinese_message := "磁盘拔出"
		return message, chinese_message
	case "disk.plugged":
		message := "disk plugged"
		chinese_message := "磁盘插入"
		return message, chinese_message
	case "raid.created":
		message := "raid created"
		chinese_message := "创建阵列"
		return message, chinese_message
	case "raid.removed":
		message := "raid removed"
		chinese_message := "删除阵列"
		return message, chinese_message
	case "volume.created":
		message := "volume created"
		chinese_message := "创建虚拟磁盘"
		return message, chinese_message
	case "volume.removed":
		message := "volume removed"
		chinese_message := "删除虚拟磁盘"
		return message, chinese_message
	case "fs.created":
		message := "filesystem created"
		chinese_message := "创建文件系统"
		return message, chinese_message
	case "fs.removed":
		message := "filesystem removed"
		chinese_message := "删除文件系统"
		return message, chinese_message
	case "raid.degraded":
		message := "raid degraded"
		chinese_message := "阵列降级"
		return message, chinese_message
	case "raid.failed":
		message := "raid failed"
		chinese_message := "阵列损坏"
		return message, chinese_message
	case "volume.failed":
		message := "volume failed"
		chinese_message := "虚拟磁盘损坏"
		return message, chinese_message
	case "raid.normal":
		message := "raid normal"
		chinese_message := "阵列恢复正常"
		return message, chinese_message
	case "volume.normal":
		message := "volume normal"
		chinese_message := "虚拟磁盘恢复正常"
		return message, chinese_message
	case "safety.created":
		message := "safety created"
		chinese_message := "开启数据保险箱"
		return message, chinese_message
	case "info.warning":
		message := "info warning"
		chinese_message := "负载过高"
		return message, chinese_message
	case "cmd.client.add":
		message := "cmd.client.add"
		chinese_message := "创建客户端"
		return message, chinese_message
	case "cmd.client.remove":
		message := "cmd.client.remove"
		chinese_message := "停用客户端"
		return message, chinese_message
	default:
		return "", "未知"
	}
}
