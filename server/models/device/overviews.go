package device

import (
	"aserver/models"
	_ "errors"
	"fmt"
	"github.com/astaxie/beego/orm"
	"time"
)

type View struct {
	NumOfDisks      int64
	NumOfRaids      int64
	NumOfVols       int64
	NumOfFs         int64
	NumOfInitiators int64
	Jours           []ResEmergency `json:"journals"`
	NumOfJours      int64
}

type ResEmergency struct {
	Uid            int       `json:"uid"`
	Created        time.Time `orm:"index" json:"created"`
	Unix           int64     `json:"unix"`
	Ip             string    `json:"ip"`
	Event          string    `json:"event"`
	MachineId      string    `json:"machineId"`
	Devtype        string    `json:"devtype"`
	Level          string    `json:"level"`
	ChineseMessage string    `json:"chinese_message"`
	Status         bool      `json:"status"`
}

// GetAllDevices retrieves all Machine matches certain condition.
// Returns empty list if no records exist.
func GetOverViews() (views View, err error) {
	o := orm.NewOrm()
	es := make([]ResEmergency, 0)

	disks_num, err := o.QueryTable(new(models.Disks)).Count()
	if err != nil {
		models.AddLog(err)
	}

	raids_num, err := o.QueryTable(new(models.Raids)).Count()
	if err != nil {
		models.AddLog(err)
	}

	vols_num, err := o.QueryTable(new(models.Volumes)).Count()
	if err != nil {
		models.AddLog(err)
	}

	fs_num, err := o.QueryTable(new(models.Fs)).Count()
	if err != nil {
		models.AddLog(err)
	}

	inits_num, err := o.QueryTable(new(models.Initiators)).Count()
	if err != nil {
		models.AddLog(err)
	}

	emergencys_num, err := o.QueryTable(new(models.Emergency)).Count()
	if err != nil {
		models.AddLog(err)
	}

	emergencys := make([]models.Emergency, 0) //TODO emergency
	if _, err = o.QueryTable(new(models.Emergency)).Filter("status", 0).All(&emergencys); err != nil {
		return
	}

	for _, i := range emergencys {
		var one models.Machine
		if _, err = o.QueryTable(new(models.Machine)).Filter("ip", i.Ip).All(&one); err != nil {
			return
		}

		var jour ResEmergency
		jour.Uid = i.Id
		jour.Created = i.CreatedAt
		jour.Unix = i.CreatedAt.Unix()
		jour.Event = i.Event
		jour.Level = i.Level
		jour.ChineseMessage = i.ChineseMessage
		jour.Status = i.Status
		jour.MachineId = one.Uuid
		jour.Ip = one.Ip
		jour.Devtype = one.Devtype
		es = append(es, jour)
	}

	fmt.Println(disks_num, raids_num, vols_num, fs_num, inits_num)
	views = View{NumOfDisks: disks_num, NumOfRaids: raids_num, NumOfVols: vols_num, NumOfFs: fs_num, NumOfInitiators: inits_num, Jours: es, NumOfJours: emergencys_num}
	return

}
