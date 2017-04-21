package models

import (
	"aserver/models/device"
	"aserver/models/nsq"
	"github.com/astaxie/beego/orm"
	"net"
	"time"
)

const (
	//monitor = "9000" //Yan
	monitor     = "8081" //TVT
	storages    = "8081"
	exportName  = "export"
	storageName = "storage"
)

func Outline() {
	go func() error {
		for {
			o := orm.NewOrm()

			time.Sleep(5 * time.Second)
			ones := make([]device.Machine, 0)
			if _, err := o.QueryTable("machine").Filter("status", 0).All(&ones); err != nil {
				return err
			}
			for _, val := range ones {
				if val.Devtype == exportName {
					err := checkSpeedio(val.Ip, monitor)
					if err == nil {
						Response(val.Ip, monitor, exportName)
					}
				} else {
					err := checkSpeedio(val.Ip, storages)
					if err == nil {
						Response(val.Ip, storages, storageName)
					}
				}

			}
		}
	}()
}

func Online() {
	go func() error {
		for {
			o := orm.NewOrm()

			time.Sleep(2 * time.Second)
			ones := make([]device.Machine, 0)
			if _, err := o.QueryTable("machine").Filter("status", 1).All(&ones); err != nil {
				return err
			}
			for _, val := range ones {
				if val.Devtype == exportName {
					err := checkSpeedio(val.Ip, monitor)
					if err != nil {
						noResponse(val.Ip, monitor, exportName)
					}
				} else {
					err := checkSpeedio(val.Ip, storages)
					if err != nil {
						noResponse(val.Ip, storages, storageName)
					}
				}
			}
		}
	}()
}

func checkSpeedio(ip, port string) error {
	conn, err := net.DialTimeout("tcp", ip+":"+port, time.Second*1)
	if err != nil {
		return err
	}
	conn.Close()
	return nil
}

func Response(machine, port, devtype string) error {
	o := orm.NewOrm()

	count := 0
	for i := 0; i < 5; i++ {
		err := checkSpeedio(machine, port)
		if err == nil {
			count += 1
		}
	}
	if count > 3 {
		var one device.Machine
		if _, err := o.QueryTable("machine").Filter("devtype", devtype).Filter("ip", machine).All(&one); err != nil {
			return err
		}
		one.Status = true
		if _, err := o.Update(&one); err != nil {
			return err
		}
		nsq.NsqRequest("ping.online", machine, "true", "CloudEvent")

	}
	return nil
}

func noResponse(machine, port, devtype string) error {
	o := orm.NewOrm()

	count := 0
	for i := 0; i < 5; i++ {
		err := checkSpeedio(machine, port)
		if err != nil {
			count += 1
		}
	}
	if count > 3 {
		var one device.Machine
		if _, err := o.QueryTable("machine").Filter("ip", machine).Filter("devtype", devtype).All(&one); err != nil {
			return err
		}
		one.Status = false
		if _, err := o.Update(&one); err != nil {
			return err
		}
		if one.Role == "master" || one.Ip == "192.168.2.144" {
			nsq.NsqRequest("ping.offline", machine, "true", "CloudEvent")
			//  NsqRequest("safety.created", machine, "true", "CloudEvent")
		} else {
			nsq.NsqRequest("ping.offline", machine, "true", "CloudEvent")
		}
	}
	return nil

}
