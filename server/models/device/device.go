package device

import (
	"aserver/models"
	"errors"
	_ "fmt"
	"github.com/astaxie/beego/orm"
	"strings"
	"time"
)

func InsertDevice(ip, version, size, devtype, cluster string) error {
	o := orm.NewOrm()

	var base models.Client
	uran := models.Urandom()
	uuid := uran + "zip" + strings.Join(strings.Split(ip, "."), "")
	base.Uuid = uuid
	base.Ip = ip
	base.Version = version
	base.Size = size
	//base.Clusterid = cluster
	base.Status = 0
	base.Devtype = devtype
	base.Created = time.Now()

	if devtype == "export" {
		var one models.Export
		num, err := o.QueryTable("export").Filter("ip", ip).All(&one)
		if err != nil {
			return err
		}
		if num == 0 {
			one.Exportinit = base
			if _, err := o.Insert(&one); err != nil {
				return err
			}
		} else {
			return errors.New("Ip address already exits")
		}

	} else if devtype == "storage" {
		var one models.Storage
		num, err := o.QueryTable("storage").Filter("ip", ip).All(&one)
		if err != nil {
			return err
		}
		if num == 0 {
			one.Exportinit = base
			if _, err := o.Insert(&one); err != nil {
				return err
			}
		} else {
			return errors.New("Ip address already exits")
		}

	} else if devtype == "client" {
		var one models.Client
		num, err := o.QueryTable("client").Filter("ip", ip).All(&one)
		if err != nil {
			return err
		}
		if num == 0 {
			one.Exportinit = base
			if _, err := o.Insert(&one); err != nil {
				return err
			}
		} else {
			return errors.New("Ip address already exits")
		}

	}

	return nil
}

func SelectAllDevices() ([]interface{}, error) {
	//get all setting  devices ,created
	o := orm.NewOrm()
	devs := make([]interface{}, 0)
	var exports []models.Export
	if _, err := o.QueryTable("export").All(&exports); err != nil {
		return devs, err
	}
	var storages []models.Storage
	if _, err := o.QueryTable("storage").All(&storages); err != nil {
		return devs, err
	}
	var clients []models.Client
	if _, err := o.QueryTable("client").All(&clients); err != nil {
		return devs, err
	}
	for _, i := range exports {
		devs = append(devs, i)
	}
	for _, i := range storages {
		devs = append(devs, i)
	}
	for _, i := range clients {
		devs = append(devs, i)
	}
	return devs, nil
}
