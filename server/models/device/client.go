package device

import (
	"aserver/models/nsq"
	"aserver/models/util"

	"errors"
	"fmt"
	"github.com/astaxie/beego/orm"
	"strings"
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

type ConClient struct {
	Ip     string
	Status bool
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

func UpdateClient(cid string, clients []ConClient) (err error) {
	o := orm.NewOrm()

	fmt.Printf("%+v", clients)
	for _, client := range clients {

		if client.Status {

			var c Client
			num, err := o.QueryTable(new(Client)).Filter("clusterid", cid).Filter("ip", client.Ip).All(&c)
			if err != nil {
				util.AddLog(err)
				return err
			}

			if num > 0 && !c.Status {
				if err = OpenClient(c.Ip, cid); err != nil {
					util.AddLog(err)
					return err
				}
				//when ip is new && going to open
			} else if num == 0 {
				//open
				if err = OpenClient(client.Ip, cid); err != nil {
					util.AddLog(err)
					return err
				}
			}
		} else {
			var c Client
			num, err := o.QueryTable(new(Client)).Filter("clusterid", cid).Filter("ip", client.Ip).All(&c)
			if err != nil {
				util.AddLog(err)
				return err
			}

			if num == 0 {
				continue
				//remove client
			} else {
				nsq.NsqRequest("cmd.client.remove", client.Ip, "true", "storages")
			}
		}
	}
	return
}

//POST create one client
func OpenClient(ip, cid string) (err error) {
	o := orm.NewOrm()

	var c Client
	var export string
	num, err := o.QueryTable(new(Client)).Filter("ip", ip).All(&c)
	if err != nil {
		util.AddLog(err)
		return
	}

	//whether in use
	if num == 0 {
		AddClient(ip, cid)
	} else {
		if c.Status {
			err = errors.New("client is in use")
			util.AddLog(err)
			return
		}
	}

	//get cluster's infos
	clus, err := GetClustersByCid(cid)
	if err != nil {
		util.AddLog(err)
		return
	}

	for _, dev := range clus.Device {
		if dev.Devtype == "export" {
			export = dev.Ip
		}
	}

	if err = util.JudgeIp(export); err == nil {
		nsq.NsqRequest("cmd.client.add", ip, export, "storages")
	} else {
		util.AddLog(err)
		return
	}
	return
}

func AddClient(ip, cid string) (err error) {
	o := orm.NewOrm()

	var one Client
	uran := util.Urandom()
	uuid := uran + "zip" + strings.Join(strings.Split(ip, "."), "")
	one.Uuid = uuid
	one.Ip = ip
	one.Version = "ZS2000"
	one.Size = "4U"
	one.Status = false
	one.Devtype = "client"
	one.Created = time.Now()
	one.Clusterid = cid

	if _, err = o.Insert(&one); err != nil {
		util.AddLog(err)
		return err
	}
	return
}

//POST delete one client
/*
func DelClient(cid string) (err error) {
	o := orm.NewOrm()

	export, storages := _GetZoofs(cid)

	var e Export
	o.QueryTable(new(Export)).Filter("ip", export).All(&e)
	//nsq.NsqRequest("cmd.client.remove", client, "true", "storages")
	for _, host := range storages {
		nsq.NsqRequest("cmd.storage.remove", host, "true", "storages")
	}
	DelZoofs(e.Uuid) //export's uuid

	return
}*/

//POST delete one client
func DelClient(ip string) (err error) {
	o := orm.NewOrm()

	//whether vaild Ip
	if err = util.JudgeIp(ip); err != nil {
		util.AddLog(err)
		return
	}

	//whether in use
	var c Client
	if _, err = o.QueryTable(new(Client)).Filter("ip", ip).All(&c); err != nil {
		util.AddLog(err)
		return
	}

	if !c.Status {
		err = errors.New("client is not in use ")
		util.AddLog(err)
		return
	}

	nsq.NsqRequest("cmd.client.remove", ip, "true", "storages")
	return
}
