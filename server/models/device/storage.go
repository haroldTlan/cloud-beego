package device

import (
	"aserver/models/nsq"
	"aserver/models/util"

	"fmt"
	"github.com/astaxie/beego/orm"
	"strconv"
)

type Rest struct {
	Ip    string `json:"ip"`
	Level string `json:"level"`
	Loc   string `json:"loc"`
}

type Storage struct {
	ExportInit
	Master string `json:"master"`
	Cid    int    `json:"cid"`
	Sid    int    `json:"sid"`
	Slot   string `json:"slot"`
}

func (t *Storage) TableName() string {
	return "storage"
}

func init() {
	orm.RegisterModel(new(Storage))
}

func RestInit(v []Rest) (err error) {
	setId := util.Urandom()
	for _, host := range v {
		msg := StorageMsg(host, len(v), setId)
		nsq.NewNsqRequest("storages", msg)
		//detail := host.Level + "*" + host.Loc //strings.Join(host.Level, host.Loc, "*")
		//nsq.NsqRequest("cmd.storage.build", host.Ip, detail, "storages")
	}

	return
}

func StorageMsg(host Rest, count int, setId string) (msg nsq.StorageNsq) {
	o := orm.NewOrm()
	level, _ := strconv.Atoi(host.Level)
	msg = nsq.StorageNsq{Event: "cmd.storage.build", Ip: host.Ip, Loc: host.Loc, Level: level, Mount: "", Count: count, Id: setId}

	var one Storage
	var export string
	o.QueryTable(new(Storage)).Filter("ip", host.Ip).All(&one)
	clus, _ := GetClustersByCid(one.Clusterid)
	for _, dev := range clus.Device {
		if dev.Devtype == "export" {
			export = dev.Ip
		}
	}

	configs, _ := CliNodeConfig(export)

	cid := 1

	for _, sd := range configs.RozoDetail.Storaged {
		if sd.Ip == host.Ip {
			for _, s := range sd.Storage {
				if s.Cid == cid {
					fmt.Printf("%+v\n", sd)
					msg.Mount = s.Root + "/0"
				}
			}

		}
	}
	return
}

func RestRemove(clusterid string) (err error) {
	fmt.Println(clusterid)

	return
}

//when zoofs created success
//
func InsertStorages(export string, ip string, cid int, sid int, slot string) error {
	o := orm.NewOrm()

	var one Storage
	num, err := o.QueryTable("storage").Filter("ip", ip).All(&one)
	if err != nil {
		return err
	}

	one.Cid = cid
	one.Sid = sid
	one.Slot = slot
	one.Master = export
	one.Status = true
	if num == 0 {
		if _, err := o.Insert(&one); err != nil {
			return err
		}
	} else {
		if _, err := o.Update(&one); err != nil {
			return err
		}
	}
	return nil
}
