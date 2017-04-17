package device

import (
	"aserver/models"
	"errors"
	_ "fmt"
	"github.com/astaxie/beego/orm"
	"regexp"
	"strings"
	"time"
)

// AddDevice insert a new Device(export, storage, client)
// into database and returns errs
func AddDevice(ip, version, size, devtype, cluster string) (err error) {
	o := orm.NewOrm()

	if m, _ := regexp.MatchString("^[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}$", ip); !m {
		err = errors.New("not validate IP address")
		models.AddLog(err)
		return
	}

	var base models.ExportInit
	uran := models.Urandom()
	uuid := uran + "zip" + strings.Join(strings.Split(ip, "."), "")
	base.Uuid = uuid
	base.Ip = ip
	base.Version = version
	base.Size = size
	base.Status = true
	base.Devtype = devtype
	base.Created = time.Now()
	//base.Clusterid = cluster

	if devtype == "export" {
		var one models.Export
		num, err := o.QueryTable("export").Filter("ip", ip).All(&one)
		if err != nil {
			models.AddLog(err)
			return err
		}
		if num == 0 {
			one.ExportInit = base
			if _, err = o.Insert(&one); err != nil {
				models.AddLog(err)
				return err
			}
		} else {
			err = errors.New("Ip address already exits")
			models.AddLog(err)
			return err
		}

	} else if devtype == "storage" {
		var one models.Storage
		num, err := o.QueryTable("storage").Filter("ip", ip).All(&one)
		if err != nil {
			models.AddLog(err)
			return err
		}
		if num == 0 {
			one.ExportInit = base
			if _, err = o.Insert(&one); err != nil {
				models.AddLog(err)
				return err
			}
		} else {
			err = errors.New("Ip address already exits")
			models.AddLog(err)
			return err
		}

	} else if devtype == "client" {
		var one models.Client
		num, err := o.QueryTable("client").Filter("ip", ip).All(&one)
		if err != nil {
			models.AddLog(err)
			return err
		}
		if num == 0 {
			one.ExportInit = base
			if _, err = o.Insert(&one); err != nil {
				models.AddLog(err)
				return err
			}
		} else {
			err = errors.New("Ip address already exits")
			models.AddLog(err)
			return err
		}

	} else {
		err = errors.New("devtype type not set")
		models.AddLog(err)
		return err
	}

	return nil
}

// GetAllDevices retrieves all Machine matches certain condition.
// Returns empty list if no records exist.
func GetAllDevices() (devs []interface{}, err error) {
	o := orm.NewOrm()
	devs = make([]interface{}, 0)
	var exports []models.Export
	if _, err = o.QueryTable("export").All(&exports); err != nil {
		models.AddLog(err)
		return
	}
	var storages []models.Storage
	if _, err = o.QueryTable("storage").All(&storages); err != nil {
		models.AddLog(err)
		return
	}
	var clients []models.Client
	if _, err = o.QueryTable("client").All(&clients); err != nil {
		models.AddLog(err)
		return
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
	return
}

// DeleteDevice deletes Device by Uuid and returns error if
// the record to be deleted doesn't exist
//TODO when delete the same
func DeleteDevice(uuid string) (err error) {
	o := orm.NewOrm()
	if _, err = o.QueryTable("export").Filter("uuid", uuid).Delete(); err != nil {
		models.AddLog(err)
		return
	}
	if _, err = o.QueryTable("storage").Filter("uuid", uuid).Delete(); err != nil {
		models.AddLog(err)
		return
	}
	if _, err = o.QueryTable("client").Filter("uuid", uuid).Delete(); err != nil {
		models.AddLog(err)
		return
	}
	return nil
}
