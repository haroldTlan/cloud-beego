package device

import (
	"aserver/models/util"
	"errors"
	"fmt"
	"github.com/astaxie/beego/orm"
)

func CliClearAllRozo(export string) (err error) {
	o := orm.NewOrm()

	var e Export
	if _, err = o.QueryTable("export").Filter("uuid", export).All(&e); err != nil { //TODO
		return
	}

	eRemove := fmt.Sprintf("zoofs export remove  %s -E %s --force", "1", e.Ip)
	eResult, err := rozoCmd(eRemove)
	if err != nil {
		err = errors.New(eResult)
		util.AddLog(err)
		return
	}

	if errorCon(eResult) {
		err = errors.New(eResult)
		util.AddLog(err)
		return
	}

	vRemove := fmt.Sprintf("zoofs volume remove -v %s -E %s", "1", e.Ip)
	vol, err := rozoCmd(vRemove)
	if err != nil {
		err = errors.New(vol)
		util.AddLog(err)
		return
	}

	if errorCon(vol) {
		err = errors.New(vol)
		util.AddLog(err)
		return
	}

	ClearZoofs(e.Clusterid)
	var clu Cluster //make zoofs false
	if _, err = o.QueryTable("cluster").Filter("uuid", e.Clusterid).All(&clu); err != nil {
		return
	}
	clu.Zoofs = false
	o.Update(&clu)

	return
}

func ClearZoofs(cid string) (err error) {
	var devs map[string][]string
	clus, _ := GetClusters()
	for _, clu := range clus {
		if cid == clu.Uuid {
			devs = clu.Devices
		}
	}

	for key, val := range devs {
		fmt.Println(key, val)

		if key == "export" {
			_clearExport(val)
		}

		if key == "storage" {
			_clearStorage(val)
		}

		if key == "client" {
			continue
		}

	}
	return
}

func _clearExport(hosts []string) (err error) {
	o := orm.NewOrm()

	for _, host := range hosts {
		var e Export
		if _, err = o.QueryTable("export").Filter("ip", host).All(&e); err != nil { //TODO
			return
		}
		e.Status = false
		if _, err := o.Update(&e); err != nil {
			util.AddLog(err)
		}
	}
	return
}

func _clearStorage(hosts []string) (err error) {
	o := orm.NewOrm()

	for _, host := range hosts {
		var s Storage
		if _, err = o.QueryTable("storage").Filter("ip", host).All(&s); err != nil { //TODO
			return
		}
		s.Status = false
		s.Master = ""
		s.Cid = 0
		s.Sid = 0
		s.Slot = ""
		if _, err := o.Update(&s); err != nil {
			util.AddLog(err)
		}
	}
	return
}
