package device

import (
	"aserver/models/nsq"
	"errors"
	"github.com/astaxie/beego/orm"
	"time"
)

type ExportInit struct {
	Id        int       `orm:"column(uid);auto" json:"uid"`
	Uuid      string    `orm:"column(uuid);size(64);null" json:"uuid"`
	Ip        string    `orm:"column(ip);size(64);null" json:"ip"`
	Version   string    `orm:"column(version);size(64);null" json:"version"`
	Size      string    `orm:"column(size);size(64);null" json:"size"`
	Clusterid string    `orm:"column(clusterid);size(64);null" json:"clusterid"`
	Status    bool      `orm:"column(status);null" json:"status"`
	Created   time.Time `orm:"column(created);type(datetime);null" json:"created"`
	Devtype   string    `orm:"column(devtype);size(64);null" json:"devtype"`
}

type Client struct {
	ExportInit
}

func (t *Client) TableName() string {
	return "client"
}

func init() {
	orm.RegisterModel(new(Client))
}

func AddClient(ip string) (err error) {
	o := orm.NewOrm()

	var c Client
	if _, err = o.QueryTable("client").Filter("ip", ip).All(&c); err != nil { //TODO
		return
	}

	if c.Status {
		err = errors.New("client has been opened")
		return
	}

	var devs map[string][]string
	clus, _ := GetClusters()
	for _, clu := range clus {
		if c.Clusterid == clu.Uuid {
			devs = clu.Devices
		}
	}

	export := devs["export"][0]

	nsq.NsqRequest("cmd.client.add", ip, export, "storages")
	return
}

func DelClient(cid string) (err error) {
	o := orm.NewOrm()

	export, client, storages := _GetZoofs(cid)

	var e Export
	o.QueryTable(new(Export)).Filter("ip", export).All(&e)
	nsq.NsqRequest("cmd.client.remove", client, "true", "storages")
	for _, host := range storages {
		nsq.NsqRequest("cmd.storage.remove", host, "true", "storages")
	}
	DelZoofs(e.Uuid) //export's uuid

	return
}

//POST delete one client
/*func DelClient(cid string) (err error) {
	var devs map[string][]string
	clus, _ := GetClusters()
	for _, clu := range clus {
		if cid == clu.Uuid {
			devs = clu.Devices
		}
	}

	for key, val := range devs {
		if key == "client" {
			for _, c := range val {
				nsq.NsqRequest("cmd.client.remove", c, "true", "storages")
			}
		}
	}

	return
}*/
