package models

import (
	/*"errors"
	"fmt"
	"reflect"
	"regexp"
	"strings"
	"time"*/
	"github.com/astaxie/beego/orm"
	"strings"
)

type StoreViews struct {
	RestDisks   []Disks    `json:"disks"`
	RestRaids   []Raids    `json:"raids"`
	RestVolumes []Volumes  `json:"volumes"`
	RestFs      []Fs       `json:"filesystems"`
	RestInits   []Inits    `json:"initiators"`
	RestJours   []Journals `json:"journals"`
	Uuid        string     `json:"uuid"`
	Type        string     `json:"devtype"`
}

func (t *StoreViews) TableName() string {
	return "machinedetails"
}

func init() {
	//orm.RegisterModel(new(Machine), new(Disks), new(Raids), new(Volumes), new(Initiators), new(Fs), new(Journals))
}

// RestApi get all storages's rest api. Returns empty list if
// no records exist
func RestApi() (storages []StoreViews, err error) {
	o := orm.NewOrm()
	var ones []Machine
	storages = make([]StoreViews, 0)
	if _, err = o.QueryTable("machine").Filter("devtype", "storage").Filter("status", 1).All(&ones); err != nil { //decide update or not
		return
	}
	for _, val := range ones {
		storage, err := restApi(val.Uuid)
		if err != nil {
			return storages, err
		}
		storages = append(storages, storage)
	}
	return
}

func restApi(uuid string) (store StoreViews, err error) {
	o := orm.NewOrm()

	disks := make([]Disks, 0)
	raids := make([]Raids, 0)
	vols := make([]Volumes, 0)
	initiators := make([]Initiators, 0)
	inits := make([]Inits, 0)
	fs := make([]Fs, 0)
	jours := make([]Journals, 0)

	if _, err = o.QueryTable(new(Disks)).Filter("machineid__exact", uuid).All(&disks); err != nil {
		return
	}
	if _, err = o.QueryTable(new(Raids)).Filter("machineid__exact", uuid).All(&raids); err != nil {
		return
	}
	if _, err = o.QueryTable(new(Volumes)).Filter("machineid__exact", uuid).All(&vols); err != nil {
		return
	}
	if _, err = o.QueryTable(new(Fs)).Filter("machineid__exact", uuid).All(&fs); err != nil {
		return
	}
	if _, err = o.QueryTable(new(Journals)).Filter("machineid__exact", uuid).All(&jours); err != nil {
		return
	}
	if _, err = o.QueryTable(new(Initiators)).Filter("machineid__exact", uuid).All(&initiators); err != nil {
		return
	}

	for _, init := range initiators {
		var i Inits
		i.Wwn = init.Wwn
		i.Id = init.Id
		i.Active = init.Active
		i.Machineid = init.Machineid
		i.Portals = strings.Split(init.Portals, "*")
		i.Volumes = strings.Split(init.Volumes, "*")
		inits = append(inits, i)
	}

	store.RestDisks = disks
	store.RestRaids = raids
	store.RestVolumes = vols
	store.RestFs = fs
	store.RestInits = inits
	store.RestJours = jours
	store.Uuid = uuid
	store.Type = "storage"

	return store, nil
}
