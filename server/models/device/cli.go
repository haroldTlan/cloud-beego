package device

import (
	"aserver/models/util"
	"github.com/astaxie/beego/orm"
)

type RozoRes struct {
	Status     bool `json:"status"`
	RozoDetail `json:"detail"`
}

type RozoDetail struct {
	Exportd  `json:"exportd"`
	Storaged []ConfStoraged `json:"storaged"`
}

type Exportd struct {
	Volume []ConfVol    `json:"volume"`
	Export []ConfExport `json:"export"`
	Ip     string       `json:"ip"`
}

type ConfVol struct {
	Vid  int       `json:"vid"`
	Cid  int       `json:"cid"`
	Sids []ConfSid `json:"sid"`
}

type ConfSid struct {
	Ip  string `json:"ip"`
	Sid int    `json:"sid"`
}

type ConfExport struct {
	Root string `json:"root"`
	Vid  int    `json:"vid"`
}

type ConfStoraged struct {
	Ip      string        `json:"ip"`
	Storage []ConfStorage `json:"storage"`
}

type ConfStorage struct {
	Cid  int    `json:"cid"`
	Sid  int    `json:"sid"`
	Root string `json:"root"`
}

func CliClearAllRozo(export string) (err error) {
	o := orm.NewOrm()

	eRemove := make([]string, 0)
	vRemove := make([]string, 0)

	var e Export
	if _, err = o.QueryTable("export").Filter("ip", export).All(&e); err != nil { //TODO
		return
	}
	//TODO volume=1, export=1
	eRemove = append(eRemove, "export", "remove", "1", "-E", e.Ip, "--force")
	vRemove = append(vRemove, "volume", "remove", "-v", "1", "-E", e.Ip)

	if _, err = rozoCmd("zoofs", eRemove); err != nil {
		util.AddLog(err)
		return
	}

	if _, err = rozoCmd("zoofs", vRemove); err != nil {
		util.AddLog(err)
		return
	}

	//TODO
	ClearZoofs(e.Clusterid)

	var clu Cluster //make zoofs false
	if _, err = o.QueryTable("cluster").Filter("uuid", e.Clusterid).All(&clu); err != nil {
		return
	}
	clu.Zoofs = false
	if _, err = o.Update(&clu); err != nil {
		util.AddLog(err)
		return
	}

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
