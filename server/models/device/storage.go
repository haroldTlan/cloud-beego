package device

import (
	"aserver/models/nsq"
	"aserver/models/util"

	_ "fmt"
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

// Gui's order
// machine's ip, disks's slot(host.Loc), raid's level,
func RestInit(v []Rest) (err error) {
	setId := util.Urandom()
	for _, host := range v {
		msg := StorageMsg(host, len(v), setId)
		nsq.NewNsqRequest("storage", msg)
		//detail := host.Level + "*" + host.Loc //strings.Join(host.Level, host.Loc, "*")
		//nsq.NsqRequest("cmd.storage.build", host.Ip, detail, "storages")
	}

	return
}

// Get storage's infos
// Mountpoint, Setting id(like uuid)
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

	configs, err := CliNodeConfig(export)
	if err != nil {
		util.AddLog(err)
		return
	}

	cid := 1 //TODO

	for _, sd := range configs.RozoDetail.Storaged {
		if sd.Ip == host.Ip {
			for _, s := range sd.Storage {
				if s.Cid == cid {
					msg.Mount = s.Root + "/0"
				}
			}
		}
	}
	return
}

// TODO
func RestRemove(a string) (err error) {
	return
}

// when zoofs created success
//
func InsertStorages(export string, ip string, cid int, sid int, slot string) (err error) {
	o := orm.NewOrm()

	var one Storage
	if _, err = o.QueryTable("storage").Filter("ip", ip).All(&one); err != nil {
		return
	}

	one.Cid = cid
	one.Sid = sid
	one.Slot = slot
	one.Master = export
	one.Status = true
	if _, err = o.Update(&one); err != nil {
		util.AddLog(err)
		return
	}

	return
}
