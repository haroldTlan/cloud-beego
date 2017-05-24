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

type ConfClient struct {
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

func UpdateClient(cid string, clients []ConfClient) (err error) {
	setId := util.Urandom()
	client, err := SelectClientIP(cid, clients)
	if err != nil {
		util.AddLog(err)
		return
	}

	for _, c := range client["open"] {
		if err = OpenClient(c, cid, setId, len(client["open"])); err != nil {
			util.AddLog(err)
			return err
		}
	}

	for _, c := range client["close"] {
		msg := nsq.ClientNsq{Event: "cmd.client.remove", Ip: c, Count: len(client["close"]), Id: setId}
		fmt.Printf("\n%+v", msg)
		nsq.NewNsqRequest("storages", msg)
		//	nsq.NsqRequest("cmd.client.remove", c, "true", "storages")
	}
	return
}

//select open or close client's ip
func SelectClientIP(cid string, cs []ConfClient) (clients map[string][]string, err error) {
	o := orm.NewOrm()
	clients = make(map[string][]string)
	clients["open"] = make([]string, 0)
	clients["close"] = make([]string, 0)

	for _, client := range cs {
		var c Client
		//GUI select the ip
		if client.Status {
			num, err := o.QueryTable(new(Client)).Filter("clusterid", cid).Filter("ip", client.Ip).All(&c)
			if err != nil {
				util.AddLog(err)
				return clients, err
			}
			//sql did not have, create and open
			if num == 0 {
				if err = AddClient(client.Ip, cid); err != nil {
					util.AddLog(err)
					return clients, err
				}
				clients["open"] = append(clients["open"], client.Ip)
			} else {
				//the client has been opened, then continue
				if c.Status {
					continue
				} else {
					clients["open"] = append(clients["open"], client.Ip)
				}
			}

			//GUI do not select the ip
		} else {
			num, err := o.QueryTable(new(Client)).Filter("clusterid", cid).Filter("ip", client.Ip).All(&c)
			if err != nil {
				util.AddLog(err)
				return clients, err
			}
			if num == 0 {
				continue

				//if true, then close
			} else {
				if c.Status {
					clients["close"] = append(clients["close"], client.Ip)
				} else {
					continue
				}
			}
		}
	}
	return
}

//POST create one client
func OpenClient(ip, cid, setId string, count int) (err error) {
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

		msg := nsq.ClientNsq{Event: "cmd.client.add", Ip: ip, Export: export, Count: count, Id: setId}
		fmt.Printf("\n%+v", msg)
		nsq.NewNsqRequest("storages", msg)
		//nsq.NsqRequest("cmd.client.add", ip, export, "storages")
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
