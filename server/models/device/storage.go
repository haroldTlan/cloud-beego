package device

import (
	"aserver/models/nsq"
	"fmt"
	"github.com/astaxie/beego/orm"
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
	for _, host := range v {
		detail := host.Level + "*" + host.Loc //strings.Join(host.Level, host.Loc, "*")
		nsq.NsqRequest("cmd.storage.build", host.Ip, detail, "storages")
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
