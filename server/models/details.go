package models

import (
	"aserver/models/device"
	"aserver/models/util"
	"github.com/astaxie/beego/orm"
	"strings"
)

//slotnr
type Dsus struct {
	Location      string `orm:"column(location);size(255);pk" json:"location"`
	SupportDiskNr int    `orm:"column(support_disk_nr)" json:"support_disk_nr"`
	Machineid     string `orm:"column(machineid);size(255)" json:"machineid"`
}

type StoreViews struct {
	ResDsus     Dsus              `json:"dsus"`
	RestDisks   []device.Disks    `json:"disks"`
	RestRaids   []device.Raids    `json:"raids"`
	RestVolumes []device.Volumes  `json:"volumes"`
	RestFs      []device.Fs       `json:"filesystems"`
	RestInits   []device.Inits    `json:"initiators"`
	RestJours   []device.Journals `json:"journals"`
	Uuid        string            `json:"uuid"`
	Ip          string            `json:"ip"`
	Type        string            `json:"devtype"`
}

func (t *StoreViews) TableName() string {
	return "machinedetails"
}

func init() {
	orm.RegisterModel(new(Dsus))
}

// RestApi get all storages's rest api. Returns empty list if
// no records exist
func RestApi() (storages []StoreViews, err error) {
	o := orm.NewOrm()
	var ones []device.Machine

	storages = make([]StoreViews, 0)
	if _, err = o.QueryTable("machine").Filter("devtype", "storage").Filter("status", 1).All(&ones); err != nil {
		util.AddLog(err)
		return
	}
	for _, val := range ones {
		storage, err := restApi(val.Uuid)
		if err != nil {
			util.AddLog(err)
			return storages, err
		}
		storages = append(storages, storage)
	}
	return
}

//single machine
func restApi(uuid string) (store StoreViews, err error) {
	o := orm.NewOrm()

	var dsus Dsus
	disks := make([]device.Disks, 0)
	raids := make([]device.Raids, 0)
	vols := make([]device.Volumes, 0)
	initiators := make([]device.Initiators, 0)
	inits := make([]device.Inits, 0)
	fs := make([]device.Fs, 0)
	jours := make([]device.Journals, 0)

	var m device.Machine
	if _, err = o.QueryTable(new(device.Machine)).Filter("uuid__exact", uuid).All(&m); err != nil {
		util.AddLog(err)
		return
	}

	if _, err = o.QueryTable(new(Dsus)).Filter("machineid__exact", uuid).All(&dsus); err != nil {
		util.AddLog(err)
		return
	}
	if _, err = o.QueryTable(new(device.Disks)).Filter("machineid__exact", uuid).All(&disks); err != nil {
		util.AddLog(err)
		return
	}
	if _, err = o.QueryTable(new(device.Raids)).Filter("machineid__exact", uuid).All(&raids); err != nil {
		util.AddLog(err)
		return
	}
	if _, err = o.QueryTable(new(device.Volumes)).Filter("machineid__exact", uuid).All(&vols); err != nil {
		util.AddLog(err)
		return
	}
	if _, err = o.QueryTable(new(device.Fs)).Filter("machineid__exact", uuid).All(&fs); err != nil {
		util.AddLog(err)
		return
	}
	if _, err = o.QueryTable(new(device.Journals)).Filter("machineid__exact", uuid).All(&jours); err != nil {
		util.AddLog(err)
		return
	}
	if _, err = o.QueryTable(new(device.Initiators)).Filter("machineid__exact", uuid).All(&initiators); err != nil {
		util.AddLog(err)
		return
	}

	for _, init := range initiators {
		var i device.Inits
		i.Wwn = init.Wwn
		i.Id = init.Id
		i.Active = init.Active
		i.Machineid = init.Machineid
		i.Portals = strings.Split(init.Portals, "*")
		i.Volumes = strings.Split(init.Volumes, "*")
		inits = append(inits, i)
	}

	store.ResDsus = dsus
	store.RestDisks = disks
	store.RestRaids = raids
	store.RestVolumes = vols
	store.RestFs = fs
	store.RestInits = inits
	store.RestJours = jours
	store.Uuid = uuid
	store.Ip = m.Ip
	store.Type = "storage"

	return store, nil
}
