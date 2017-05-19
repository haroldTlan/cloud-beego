package device

import (
	"aserver/models/nsq"
	"aserver/models/util"

	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/astaxie/beego/orm"
	"os/exec"
	"strconv"
	"strings"
	"time"
	//"gopkg.in/yaml.v2"
)

type Export struct {
	ExportInit `orm:"auto"`
}

func (t *Export) TableName() string {
	return "export"
}

func init() {
	orm.RegisterModel(new(Export))
}

//POST init rozofs's system
func Zoofs(clusterid string, l int) (err error) {
	o := orm.NewOrm()

	//Get export & storages's ip
	export, expands, _, err := _GetZoofs(clusterid)
	if err != nil {
		util.AddLog(err)
		return
	}

	//Error Handing  and init rozofs
	if err = judgeZoofs(export, expands, l); err != nil {
		util.AddLog(err)
		return
	}

	var clu Cluster //make zoofs true
	if _, err = o.QueryTable("cluster").Filter("uuid", clusterid).All(&clu); err != nil {
		return
	}
	clu.Zoofs = true
	o.Update(&clu)

	return
}

//Delete
func DelZoofs(cid string) (err error) { //need export's uuid
	export, storages, _, _ := _GetZoofs(cid)
	o := orm.NewOrm()

	//client remove
	/*for _, host := range clients {
		nsq.NsqRequest("cmd.client.remove", host, "true", "storages")
	}*/

	//storage remove
	for _, host := range storages {
		nsq.NsqRequest("cmd.storage.remove", host, "true", "storages")
	}

	//export remove
	if exist := o.QueryTable(new(Export)).Filter("ip", export).Exist(); !exist {
		err = errors.New("export is not exist")
		util.AddLog(err)
		return
	}

	if err = CliClearAllRozo(export); err != nil {
		util.AddLog(err)
		return
	}
	return
}

//Use cid to get export & expands
func _GetZoofs(cid string) (export string, expand []string, client []string, err error) {
	clus, err := GetClustersByCid(cid)
	if err != nil {
		util.AddLog(err)
		return
	}

	for _, dev := range clus.Device {
		if dev.Devtype == "export" {
			export = dev.Ip
		} else if dev.Devtype == "storage" {
			expand = append(expand, dev.Ip)
		} else if dev.Devtype == "client" {
			expand = append(client, dev.Ip)
		}
	}

	return
}

//Error Handing  and init rozofs
func judgeZoofs(export string, expands []string, l int) (err error) {
	levelJudge := map[int]bool{
		0: true, 1: true, 2: true,
	}

	//Ip error handing
	if err = util.JudgeIp(export); err != nil {
		util.AddLog(err)
		return
	}
	for _, ip := range expands {
		if err = util.JudgeIp(ip); err != nil {
			util.AddLog(err)
			return
		}
	}

	//level judging
	if !levelJudge[l] {
		return fmt.Errorf("choose from 0, 1, 2")
	}
	if l == 0 && len(expands)%4 != 0 {
		return fmt.Errorf("4 are needed for the layout 0")
	}
	if l == 1 && len(expands)%8 != 0 {
		return fmt.Errorf("8 are needed for the layout 1")
	}
	if l == 2 && len(expands)%12 != 0 {
		return fmt.Errorf("12 are needed for the layout 2")
	}

	if err = volExport(export, expands, l); err != nil {
		util.AddLog(err)
		return
	}

	return
}

//Create volume, then export
func volExport(export string, expands []string, l int) (err error) {
	exports_stop := make([]string, 0)
	volume_create := make([]string, 0)
	exports_create := make([]string, 0)
	exports_start := make([]string, 0)

	exports_stop = append(exports_stop, "node", "stop", "-E", export)
	volume_create = append(volume_create, "volume", "expand")
	for _, i := range expands {
		volume_create = append(volume_create, i)
	}
	volume_create = append(volume_create, "--vid", "1", "--layout", strconv.Itoa(l), "--exportd", export)
	exports_create = append(exports_create, "export", "create", "1", "-E", export)
	exports_start = append(exports_start, "node", "start", "-E", export)

	if _, err = rozoCmd("zoofs", exports_stop); err != nil {
		util.AddLog(err)
		return
	}

	time.Sleep(2 * time.Second)
	if _, err = rozoCmd("zoofs", volume_create); err != nil {
		util.AddLog(err)
		return
	}

	time.Sleep(2 * time.Second)
	if _, err = rozoCmd("zoofs", exports_create); err != nil {
		util.AddLog(err)
		return
	}

	time.Sleep(2 * time.Second)
	if _, err = rozoCmd("zoofs", exports_start); err != nil {
		util.AddLog(err)
		return
	}

	err = zoofsInsert(export, expands)
	if err != nil {
		util.AddLog(err)
		return
	}
	return
}

//Change export and storages's details
func zoofsInsert(export string, expands []string) (err error) {
	if err = InsertExports(export); err != nil {
		util.AddLog(err)
		return
	}

	configs, err := CliNodeConfig(export)
	if err != nil {
		util.AddLog(err)
		return
	}

	for _, val := range expands {
		cid, sid, slot, err := CliStorageConfig(configs, val)
		if err != nil {
			util.AddLog(err)
			return err
		}
		if err := InsertStorages(export, val, cid, sid, slot); err != nil {
			util.AddLog(err)
			return err
		}
	}
	return
}

//Change Export's status
func InsertExports(ip string) error {
	o := orm.NewOrm()

	var one Export
	num, err := o.QueryTable("export").Filter("ip", ip).All(&one)
	if err != nil {
		util.AddLog(err)
		return err
	}

	if num == 0 {
		return fmt.Errorf("export not exist")
	} else {
		one.Status = true
		if _, err = o.Update(&one); err != nil {
			util.AddLog(err)
			return err
		}
	}
	return nil
}

//Get storage's cid, sid, slot
func CliStorageConfig(config RozoRes, storage string) (cid int, sid int, slot string, err error) {
	vid, cid := 1, 1
	for _, vol := range config.RozoDetail.Volume {
		if vol.Cid == cid && vol.Vid == vid {
			cid = vol.Cid
			for _, s := range vol.Sids {
				if s.Ip == storage {
					sid = s.Sid
				}
			}
		}
	}
	slot = strconv.Itoa(cid) + "_" + strconv.Itoa(sid)
	return
}

func CliNodeConfig(export string) (rozo RozoRes, err error) {
	cmdArgs := make([]string, 0)
	cmdArgs = append(cmdArgs, "rozofs.py", "--ip", export)

	outs, err := rozoCmd("python", cmdArgs)
	if err != nil {
		return
	}

	var res map[string]interface{}
	if err = json.Unmarshal([]byte(outs), &res); err != nil {
		return
	}

	if res["status"].(bool) {
		if err = json.Unmarshal([]byte(outs), &rozo); err != nil {
			return
		}
	} else {
		err = fmt.Errorf(res["detail"].(string))
		return
	}

	return
}

//Cmd
func rozoCmd(name string, cmdArgs []string) (output string, err error) {
	cmd := exec.Command(name, cmdArgs...)

	// Stdout buffer
	w := &bytes.Buffer{}
	// Attach buffer to command
	cmd.Stderr = w
	cmd.Stdout = w
	// Execute command
	err = cmd.Run() // will wait for command to return

	//Cmd's Error Handing for rozofs
	fails := []string{"FAILED", "usage", "failed"}
	for _, val := range fails {
		if strings.Index(string(w.Bytes()), val) >= 0 {
			return string(w.Bytes()), fmt.Errorf(string(w.Bytes()))
		}
	}

	return string(w.Bytes()), nil
}
