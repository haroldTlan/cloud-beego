package device

import (
	"aserver/models/util"
	"fmt"
	"github.com/astaxie/beego/orm"
	"strconv"
	"strings"
	"time"
)

type Cluster struct {
	Cid     int       `orm:"column(cid);pk"`
	Uuid    string    `orm:"column(uuid);size(255)"`
	Zoofs   bool      `orm:"column(zoofs)"`
	Store   bool      `orm:"column(store)"`
	Created time.Time `orm:"column(created);type(datetime)"`
}

type ResCluster struct {
	Cid     int                 `json:"cid"`
	Uuid    string              `json:"uuid"`
	Zoofs   bool                `json:"zoofs"`
	Store   bool                `json:"store"`
	Devices map[string][]string `json:"devices"`
	Device  []Dev               `json:"device"`
	Created time.Time           `json:"created"`
}

type Dev struct {
	Ip      string `json:"ip"`
	Uuid    string `json:"uuid"`
	Status  bool   `json:"status"`
	Devtype string `json:"devtype"`
}

type ConfigCluster struct {
	Cid      int
	Storages []ConfigStorage
}

type ConfigStorage struct {
	Sid int
	Ip  string
}

func init() {
	orm.RegisterModel(new(Cluster))
}

//GET AllClusters
func GetClusters() (res []ResCluster, err error) {
	o := orm.NewOrm()

	var clus []Cluster
	res = make([]ResCluster, 0)
	if _, err = o.QueryTable(new(Cluster)).All(&clus); err != nil {
		util.AddLog(err)
		return
	}

	for _, c := range clus {
		var clu ResCluster
		clu.Devices, clu.Device, err = _device(c.Uuid)
		clu.Cid = c.Cid
		clu.Uuid = c.Uuid
		clu.Zoofs = c.Zoofs
		clu.Store = c.Store
		clu.Created = c.Created
		res = append(res, clu)
	}

	return
}

//POST create cluster and update device's clusterid
func AddClusters(clu int, export, storage string) (err error) {
	o := orm.NewOrm()

	uran := util.Urandom()
	uuid := uran + "cid" + strconv.Itoa(clu)
	cluster := Cluster{Cid: clu, Uuid: uuid, Zoofs: false, Store: false, Created: time.Now()}

	if exist := o.QueryTable(new(Cluster)).Filter("cid", clu).Exist(); exist {
		err = fmt.Errorf("cluster id exist!")
		util.AddLog(err)
		return
	}

	if _, err = o.Insert(&cluster); err != nil {
		util.AddLog(err)
		return
	}

	//update devices's clusterid
	if err = updateDevs(export, storage, uuid); err != nil {
		util.AddLog(err)
		return
	}
	return
}

//DELETE
func DelClusters(clusterid string) (err error) {
	o := orm.NewOrm()

	if exist := o.QueryTable(new(Cluster)).Filter("uuid", clusterid).Exist(); !exist {
		err = fmt.Errorf("No cluster exist")
		util.AddLog(err)
		return
	}

	var export []Export
	if num, err := o.QueryTable(new(Export)).Filter("clusterid", clusterid).All(&export); err == nil && num > 0 {
		for _, e := range export {
			e.Clusterid = ""
			if _, err = o.Update(&e); err != nil {
				util.AddLog(err)
				return err
			}
		}
	}

	var storage []Storage
	if num, err := o.QueryTable(new(Storage)).Filter("clusterid", clusterid).All(&storage); err == nil && num > 0 {
		for _, s := range storage {
			s.Clusterid = ""
			if _, err = o.Update(&s); err != nil {
				util.AddLog(err)
				return err
			}
		}
	}

	var client []Client
	if num, err := o.QueryTable(new(Client)).Filter("clusterid", clusterid).All(&client); err == nil && num > 0 {
		for _, c := range client {
			c.Clusterid = ""
			if _, err = o.Update(&c); err != nil {
				util.AddLog(err)
				return err
			}
		}
	}

	if _, err := o.QueryTable(new(Cluster)).Filter("uuid", clusterid).Delete(); err != nil {
		util.AddLog(err)
		return err
	}
	return

}

//Get clusters by cid
func GetClustersByCid(cid string) (clu ResCluster, err error) {
	o := orm.NewOrm()

	var c Cluster
	if _, err = o.QueryTable(new(Cluster)).Filter("uuid", cid).All(&c); err != nil {
		util.AddLog(err)
		return
	}

	clu.Devices, clu.Device, err = _device(c.Uuid)
	clu.Cid = c.Cid
	clu.Uuid = c.Uuid
	clu.Zoofs = c.Zoofs
	clu.Store = c.Store
	clu.Created = c.Created

	return
}

//customize device infos in clusters
func _device(uuid string) (devs map[string][]string, dev []Dev, err error) {
	o := orm.NewOrm()
	var d Dev
	var m Machine
	devs = make(map[string][]string, 0)

	var e []Export
	if _, err = o.QueryTable(new(Export)).Filter("clusterid", uuid).All(&e); err != nil {
		util.AddLog(err)
		return
	}

	var s []Storage
	if _, err = o.QueryTable(new(Storage)).Filter("clusterid", uuid).All(&s); err != nil {
		util.AddLog(err)
		return
	}

	var c []Client
	if _, err = o.QueryTable(new(Client)).Filter("clusterid", uuid).All(&c); err != nil {
		util.AddLog(err)
		return
	}

	for _, i := range e {
		if err = o.QueryTable(new(Machine)).Filter("ip", i.Ip).One(&m); err != nil {
			util.AddLog(err)
			return
		}
		d.Ip = i.Ip
		d.Uuid = i.Uuid
		d.Status = m.Status
		d.Devtype = "export"
		dev = append(dev, d)
		devs["export"] = append(devs["export"], i.Ip)
	}
	for _, i := range s {
		if err = o.QueryTable(new(Machine)).Filter("ip", i.Ip).One(&m); err != nil {
			util.AddLog(err)
			return
		}
		d.Ip = i.Ip
		d.Uuid = i.Uuid
		d.Status = m.Status
		d.Devtype = "storage"
		dev = append(dev, d)
		devs["storage"] = append(devs["storage"], i.Ip)
	}
	for _, i := range c {
		if err = o.QueryTable(new(Machine)).Filter("ip", i.Ip).One(&m); err != nil {
			util.AddLog(err)
			return
		}
		d.Ip = i.Ip
		d.Uuid = i.Uuid
		d.Status = m.Status
		d.Devtype = "client"
		dev = append(dev, d)
		devs["client"] = append(devs["client"], i.Ip)
	}
	return
}

//update export, storage 's cid
func updateDevs(export, storage, uuid string) (err error) {
	o := orm.NewOrm()

	es := strings.Split(export, ",")
	ss := strings.Split(storage, ",")
	for _, host := range es {
		if err = util.JudgeIp(host); err != nil {
			util.AddLog(err)
			return
		}
		var e Export
		if num, err := o.QueryTable(new(Export)).Filter("ip", host).All(&e); err == nil && num > 0 {
			e.Clusterid = uuid
			if _, err = o.Update(&e); err != nil {
				util.AddLog(err)
				return err
			}
		}
	}

	for _, host := range ss {
		if err = util.JudgeIp(host); err != nil {
			util.AddLog(err)
			return
		}
		var s Storage
		if num, err := o.QueryTable(new(Storage)).Filter("ip", host).All(&s); err == nil && num > 0 {
			s.Clusterid = uuid
			if _, err = o.Update(&s); err != nil {
				util.AddLog(err)
				return err
			}
		}
	}

	return
}
