package models

import (
	_ "fmt"
	"github.com/astaxie/beego/orm"
	"strings"
	"time"
)

func init() {
	orm.RegisterModel(new(Disks), new(Raids), new(Volumes), new(Initiators), new(Fs), new(Journals), new(Dsus))
}

func AddRest(ip string, rest Rest) {
	o := orm.NewOrm()
	var m Machine
	if err := o.QueryTable(new(Machine)).Filter("devtype", "storage").Filter("ip", ip).One(&m); err != nil {
		AddLog(err)
	}
	AddDisks(rest.Disk, m.Uuid)
	AddRaids(rest.Raid, m.Uuid)
	AddVolumes(rest.Volume, m.Uuid)
	AddFs(rest.Filesystem, m.Uuid)
	AddInitiators(rest.Initiator, m.Uuid)
	AddJournals(rest.Journal, m.Uuid)
	AddDsus(rest.Dsu, m.Uuid)
}

//Each machine's disks from speedweb
func AddDisks(disks []Disks, machineid string) (err error) {
	o := orm.NewOrm()

	//when someone is out of disks
	out := make(map[string]bool, 0)
	var ds []Disks

	//ds from databases
	if _, err := o.QueryTable(new(Disks)).Filter("machineid", machineid).All(&ds); err != nil {
		AddLog(err)
	}

	//Delete when some disks disappear
	for _, d := range ds {
		out[d.Uuid] = false
		for _, now := range disks {
			if d.Uuid == now.Uuid {
				out[d.Uuid] = true
			}
		}
	}
	for k, v := range out {
		if !v {
			if _, err = o.QueryTable(new(Disks)).Filter("uuid", k).Delete(); err != nil {
				AddLog(err)
			}
		}
	}

	//Update or Insert
	for _, disk := range disks {
		disk.Machineid = machineid
		if exist := o.QueryTable(new(Disks)).Filter("machineid", machineid).Filter("uuid", disk.Uuid).Exist(); exist {
			if _, err := o.Update(&disk); err != nil {
				AddLog(err)
			}
		} else {
			if _, err := o.Insert(&disk); err != nil {
				AddLog(err)
			}
		}
	}
	return nil
}

//Each machine's raids from speedweb
func AddRaids(raids []Raids, machineid string) (err error) {
	o := orm.NewOrm()

	//when someone is out of raids
	out := make(map[string]bool, 0)
	var rs []Raids

	//rs from databases
	if _, err := o.QueryTable(new(Raids)).Filter("machineid", machineid).All(&rs); err != nil {
		AddLog(err)
	}

	//Delete when some raids disappear
	for _, r := range rs {
		out[r.Uuid] = false
		for _, now := range raids {
			if r.Uuid == now.Uuid {
				out[r.Uuid] = true
			}
		}
	}
	for k, v := range out {
		if !v {
			if _, err = o.QueryTable(new(Raids)).Filter("uuid", k).Delete(); err != nil {
				AddLog(err)
			}
		}
	}

	//Update or Insert
	for _, raid := range raids {
		raid.Machineid = machineid
		if exist := o.QueryTable(new(Raids)).Filter("machineid", machineid).Filter("uuid", raid.Uuid).Exist(); exist {
			if _, err := o.Update(&raid); err != nil {
				AddLog(err)
			}
		} else {
			if _, err := o.Insert(&raid); err != nil {
				AddLog(err)
			}
		}
	}
	return nil
}

//Each machine's vols from speedweb
func AddVolumes(vols []Volumes, machineid string) (err error) {
	o := orm.NewOrm()

	//when someone is out of vols
	out := make(map[string]bool, 0)
	var vs []Volumes

	//vs from databases
	if _, err := o.QueryTable(new(Volumes)).Filter("machineid", machineid).All(&vs); err != nil {
		AddLog(err)
	}

	//Delete when some volumes disappear
	for _, v := range vs {
		out[v.Uuid] = false
		for _, now := range vols {
			if v.Uuid == now.Uuid {
				out[v.Uuid] = true
			}
		}
	}
	for k, v := range out {
		if !v {
			if _, err = o.QueryTable(new(Volumes)).Filter("uuid", k).Delete(); err != nil {
				AddLog(err)
			}
		}
	}

	//Update or Insert
	for _, vol := range vols {
		vol.Machineid = machineid
		if exist := o.QueryTable(new(Volumes)).Filter("machineid", machineid).Filter("uuid", vol.Uuid).Exist(); exist {
			if _, err := o.Update(&vol); err != nil {
				AddLog(err)
			}
		} else {
			if _, err := o.Insert(&vol); err != nil {
				AddLog(err)
			}
		}
	}
	return nil
}

//Each machine's initiators from speedweb
func AddInitiators(inits []Inits, machineid string) (err error) {
	o := orm.NewOrm()

	//when someone is out of inits
	out := make(map[string]bool, 0)
	var is []Initiators

	//is from databases
	if _, err := o.QueryTable(new(Initiators)).Filter("machineid", machineid).All(&is); err != nil {
		AddLog(err)
	}

	//Delete when some initiators disappear
	for _, i := range is {
		out[i.Wwn] = false
		for _, now := range inits {
			if i.Wwn == now.Wwn {
				out[i.Wwn] = true
			}
		}
	}
	for k, v := range out {
		if !v {
			if _, err = o.QueryTable(new(Initiators)).Filter("wwn", k).Delete(); err != nil {
				AddLog(err)
			}
		}
	}

	//Update or Insert
	for _, init := range inits {
		var i Initiators
		i.Portals = strings.Join(init.Portals, "*")
		i.Wwn = init.Wwn
		i.Id = init.Id
		i.Volumes = strings.Join(init.Volumes, "*")
		i.Active = init.Active
		i.Machineid = machineid
		if exist := o.QueryTable(new(Initiators)).Filter("machineid", machineid).Filter("id", init.Id).Exist(); exist {

			if _, err := o.Update(&i); err != nil {
				AddLog(err)
			}
		} else {
			if _, err := o.Insert(&i); err != nil {
				AddLog(err)
			}
		}
	}
	return nil
}

//Each machine's fs from speedweb
func AddFs(fs []Fs, machineid string) (err error) {
	o := orm.NewOrm()

	//when someone is out of fs
	out := make(map[string]bool, 0)
	var files []Fs

	//rs from databases
	if _, err := o.QueryTable(new(Fs)).Filter("machineid", machineid).All(&files); err != nil {
		AddLog(err)
	}

	//Delete when some disks disappear
	for _, f := range files {
		out[f.Uuid] = false
		for _, now := range fs {
			if f.Uuid == now.Uuid {
				out[f.Uuid] = true
			}
		}
	}
	for k, v := range out {
		if !v {
			if _, err = o.QueryTable(new(Fs)).Filter("uuid", k).Delete(); err != nil {
				AddLog(err)
			}
		}
	}

	//Update or Insert
	for _, f := range fs {
		f.Machineid = machineid
		if exist := o.QueryTable(new(Fs)).Filter("machineid", machineid).Filter("uuid", f.Uuid).Exist(); exist {
			if _, err = o.Update(&f); err != nil {
				AddLog(err)
				return
			}
		} else {
			if _, err = o.Insert(&f); err != nil {
				AddLog(err)
				return
			}
		}
	}
	return
}

//Each machine's journals from speedweb
func AddJournals(js []Journals, machineid string) (err error) {
	o := orm.NewOrm()

	for _, j := range js {
		//var p []orm.Params
		//unix := strconv.FormatInt(j.Unix, 10)
		j.Machineid = machineid
		j.Created = time.Unix(j.Unix, 0)
		//sql := "select uid from `journals` where machineid='" + machineid + "' and created_at='" + unix + "' and message='" + j.Message + "' limit 1"
		//num, _ := o.Raw(sql).Values(&p)

		if exist := o.QueryTable(new(Journals)).Filter("machineid", machineid).Filter("message", j.Message).Filter("created_at", j.Unix).Exist(); exist {
			if _, err := o.Update(&j); err != nil {
				AddLog(err)
			}
		} else {
			if _, err := o.Insert(&j); err != nil {
				AddLog(err)
			}
		}
	}
	return nil
}

//Each machine's dsus from speedweb
func AddDsus(d []Dsus, machineid string) (err error) {
	o := orm.NewOrm()

	for _, lm := range d {
		lm.Machineid = machineid
		if exist := o.QueryTable(new(Dsus)).Filter("machineid", machineid).Exist(); exist {
			if _, err = o.Update(&lm); err != nil {
				AddLog(err)
			}
		} else {
			if _, err = o.Insert(&lm); err != nil {
				AddLog(err)
			}
		}
	}
	return
}
