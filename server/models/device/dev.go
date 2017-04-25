package device

import (
	"aserver/models/util"
	"errors"
	_ "fmt"
	"github.com/astaxie/beego/orm"
	"regexp"
	"strings"
	"time"
)

type Exports struct {
	Export
	Name string `json:"cluster"`
}

type Storages struct {
	Storage
	Name string `json:"cluster"`
}

type Clients struct {
	Client
	Name string `json:"cluster"`
}

// AddDevice insert a new Device(export, storage, client)
// into database and returns errs
func AddDevice(ip, version, size, devtype, cluster string) (err error) {
	o := orm.NewOrm()

	_devtype := map[string]bool{
		"export": true, "storage": true, "client": true,
	}

	if !_devtype[devtype] {
		err = errors.New("not validate devtype")
		util.AddLog(err)
		return
	}

	if m, _ := regexp.MatchString("^[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}$", ip); !m {
		err = errors.New("not validate IP address")
		util.AddLog(err)
		return
	}

	var base ExportInit
	uran := util.Urandom()
	uuid := uran + "zip" + strings.Join(strings.Split(ip, "."), "")
	base.Uuid = uuid
	base.Ip = ip
	base.Version = version
	base.Size = size
	base.Status = false
	base.Devtype = devtype
	base.Created = time.Now()
	//base.Clusterid = cluster

	if devtype == "export" {
		var one Export
		num, err := o.QueryTable("export").Filter("ip", ip).All(&one)
		if err != nil {
			util.AddLog(err)
			return err
		}
		if num == 0 {
			one.ExportInit = base
			if _, err = o.Insert(&one); err != nil {
				util.AddLog(err)
				return err
			}
		} else {
			err = errors.New("Ip address already exits")
			util.AddLog(err)
			return err
		}

	} else if devtype == "storage" {
		var one Storage
		num, err := o.QueryTable("storage").Filter("ip", ip).All(&one)
		if err != nil {
			util.AddLog(err)
			return err
		}
		if num == 0 {
			one.ExportInit = base
			if _, err = o.Insert(&one); err != nil {
				util.AddLog(err)
				return err
			}
		} else {
			err = errors.New("Ip address already exits")
			util.AddLog(err)
			return err
		}

	} else if devtype == "client" {
		var one Client
		num, err := o.QueryTable("client").Filter("ip", ip).All(&one)
		if err != nil {
			util.AddLog(err)
			return err
		}
		if num == 0 {
			one.ExportInit = base
			if _, err = o.Insert(&one); err != nil {
				util.AddLog(err)
				return err
			}
		} else {
			err = errors.New("Ip address already exits")
			util.AddLog(err)
			return err
		}

	} else {
		err = errors.New("devtype type not set")
		util.AddLog(err)
		return err
	}
	if devtype != "client" {
		AddMachine(ip, devtype, "storage", "storage", 24)
	}

	return nil
}

// GetAllDevices retrieves all Machine matches certain condition.
// Returns empty list if no records exist.
func GetAllDevices() (devs []interface{}, err error) {
	o := orm.NewOrm()
	devs = make([]interface{}, 0)
	var exports []Export
	if _, err = o.QueryTable("export").All(&exports); err != nil {
		util.AddLog(err)
		return
	}
	var storages []Storage
	if _, err = o.QueryTable("storage").All(&storages); err != nil {
		util.AddLog(err)
		return
	}
	var clients []Client
	if _, err = o.QueryTable("client").All(&clients); err != nil {
		util.AddLog(err)
		return
	}
	for _, i := range exports {
		j := Exports{Export: i}
		if i.Clusterid != "" {
			j.Name = strings.Split(i.Clusterid, "cid")[1]
		} else {
			j.Name = ""
		}
		devs = append(devs, j)
	}
	for _, i := range storages {
		j := Storages{Storage: i}
		if i.Clusterid != "" {
			j.Name = strings.Split(i.Clusterid, "cid")[1]
		} else {
			j.Name = ""
		}
		devs = append(devs, j)
	}
	for _, i := range clients {
		j := Clients{Client: i}
		if i.Clusterid != "" {
			j.Name = strings.Split(i.Clusterid, "cid")[1]
		} else {
			j.Name = ""
		}
		devs = append(devs, j)
	}
	return
}

// DeleteDevice deletes Device by Uuid and returns error if
// the record to be deleted doesn't exist
//TODO when delete the same
func DeleteDevice(uuid string) (err error) {
	o := orm.NewOrm()
	if _, err = o.QueryTable("export").Filter("uuid", uuid).Delete(); err != nil {
		util.AddLog(err)
		return
	}
	if _, err = o.QueryTable("storage").Filter("uuid", uuid).Delete(); err != nil {
		util.AddLog(err)
		return
	}
	if _, err = o.QueryTable("client").Filter("uuid", uuid).Delete(); err != nil {
		util.AddLog(err)
		return
	}
	return nil
}
