package device

import (
	"aserver/models/util"
	"bytes"
	"errors"
	"fmt"
	"github.com/astaxie/beego/orm"
	"os/exec"
	"strconv"
	"strings"
	"time"

	"gopkg.in/yaml.v2"
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

//Delete
func DelZoofs(export string) (err error) { //need export's uuid
	o := orm.NewOrm()

	if exist := o.QueryTable(new(Export)).Filter("uuid", export).Exist(); !exist {
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

func judge(export string, expands []string, l int) (err error) {
	levelJudge := map[int]bool{
		0: true, 1: true, 2: true,
	}

	if err = util.JudgeIp(export); err != nil {
		return
	}

	for _, ip := range expands {
		if err = util.JudgeIp(ip); err != nil {
			return
		}
	}
	if !levelJudge[l] {
		err = errors.New("choose from 0, 1, 2")
		return
	}

	if l == 0 && len(expands)%4 != 0 {
		return errors.New("4 are needed for the layout 0")
	}
	if l == 1 && len(expands)%8 != 0 {
		return errors.New("8 are needed for the layout 1")
	}
	if l == 2 && len(expands)%12 != 0 {
		return errors.New("12 are needed for the layout 2")
	}

	if err = volExport(export, expands, l); err != nil {
		return
	}
	return
}

func volExport(export string, hosts []string, l int) (err error) {
	exports_stop := "zoofs node stop -E " + export
	volume_create := "zoofs volume expand " + strings.Join(hosts, " ") + " --vid 1  --layout " + strconv.Itoa(l) + " --exportd " + export
	exports_create := "zoofs export create 1 -E " + export
	exports_start := "zoofs node start -E " + export

	stop, err := rozoCmd(exports_stop)
	if err != nil {
		err = errors.New(stop)
		util.AddLog(err)
		return
	}

	if errorCon(stop) {
		err = errors.New(stop)
		util.AddLog(err)
		return
	}

	time.Sleep(2 * time.Second)
	create, err := rozoCmd(volume_create)
	if err != nil {
		err = errors.New(create)
		util.AddLog(err)
		return
	}

	if errorCon(create) {
		err = errors.New(create)
		util.AddLog(err)
		return
	}

	time.Sleep(2 * time.Second)
	vol, err := rozoCmd(exports_create)
	if err != nil {
		err = errors.New(vol)
		util.AddLog(err)
		return
	}
	if errorCon(vol) {
		err = errors.New(vol)
		util.AddLog(err)
		return
	}
	time.Sleep(2 * time.Second)
	e, err := rozoCmd(exports_start)
	if err != nil {
		err = errors.New(e)
		util.AddLog(err)
		return
	}
	if errorCon(e) {
		err = errors.New(e)
		util.AddLog(err)
		return
	}

	zoofsInsert(export, hosts)
	return
}

func zoofsInsert(ip string, expands []string) (err error) {
	err = InsertExports(ip, true)
	AddMachine(ip, "export", "24")
	if err != nil {
		util.AddLog(err)
		return
	}
	for _, val := range expands {
		cid, sid, slot, err := CliStorageConfig(ip, val)
		if err != nil {
			util.AddLog(err)
			return err
		}
		if err := InsertStorages(ip, val, cid, sid, slot); err != nil {
			util.AddLog(err)
			return err
		}
		AddMachine(val, "storage", "24")
	}
	return
}

func _GetZoofs(cid string) (export, client string, storage []string) {
	var devs map[string][]string

	clus, _ := GetClusters()
	for _, clu := range clus {
		if cid == clu.Uuid {
			devs = clu.Devices
		}
	}
	fmt.Println(cid)
	fmt.Println(clus)
	export = devs["export"][0]
	storage = devs["storage"]
	client = devs["client"][0]

	return
}

//main POST
func Zoofs(clusterid string, l int) (err error) {
	o := orm.NewOrm()

	export, client, expands := _GetZoofs(clusterid)

	if err = judge(export, expands, l); err != nil {
		util.AddLog(err)
		return
	}

	var e Export
	num, err := o.QueryTable(new(Export)).Filter("ip", export).All(&e)
	if err != nil {
		util.AddLog(err)
	}
	e.Status = true

	if num == 0 {
		if _, err := o.Insert(&e); err != nil {
			util.AddLog(err)
		}
	} else {
		if _, err := o.Update(&e); err != nil {
			util.AddLog(err)
		}
	}

	for _, ex := range expands {
		var s Storage
		num, err := o.QueryTable(new(Storage)).Filter("ip", ex).All(&s)
		if err != nil {
			util.AddLog(err)
		}
		s.Status = true
		if num == 0 {
			if _, err := o.Insert(&s); err != nil {
				util.AddLog(err)
			}
		} else {
			if _, err := o.Update(&s); err != nil {
				util.AddLog(err)
			}
		}
	}

	AddClient(client)

	/*var c Client
	num, err = o.QueryTable(new(Client)).Filter("ip", client).All(&c)
	if err != nil {
		util.AddLog(err)
	}
	c.Status = true

	if num == 0 {
		if _, err := o.Insert(&c); err != nil {
			util.AddLog(err)
		}
	} else {
		if _, err := o.Update(&c); err != nil {
			util.AddLog(err)
		}
	}*/
	var clu Cluster //make zoofs true
	if _, err = o.QueryTable("cluster").Filter("uuid", clusterid).All(&clu); err != nil {
		return
	}
	clu.Zoofs = true
	o.Update(&clu)

	return
}

func InsertExports(ip string, status bool) error {
	o := orm.NewOrm()

	var one Export
	num, err := o.QueryTable("export").Filter("ip", ip).All(&one)
	if err != nil {
		return err
	}

	if num == 0 {
		uran := util.Urandom()
		uuid := uran + "zip" + strings.Join(strings.Split(ip, "."), "")
		one.Uuid = uuid
		one.Ip = ip
		one.Version = "ZS2000"
		one.Size = "4U"
		one.Status = status
		one.Created = time.Now()
		if _, err := o.Insert(&one); err != nil {
			return err
		}
	} else {
		one.Status = status
		_, err = o.Update(&one)
		if err != nil {
			return err
		}
	}
	return nil
}

func CliStorageConfig(export string, ip string) (int, int, string, error) {

	var config ConfigCluster
	configs, err := NewCliNodeConfig(export)
	if err != nil {
		return 0, 0, "", err
	}

	for _, vals := range configs {
		storages := vals.Storages
		for _, store := range storages {
			if store.Ip == ip {
				config = vals
			}
		}
	}
	cid := config.Cid
	var sid int
	for _, val := range config.Storages {
		if val.Ip == ip {
			sid = val.Sid
		}
	}
	slot := strconv.Itoa(cid) + "_" + strconv.Itoa(sid)
	return cid, sid, slot, nil
}

func NewCliNodeConfig(export string) ([]ConfigCluster, error) {
	config := make(map[string][]map[string][]map[string][]map[string][]map[string][]map[string]string)
	cmd := exec.Command("/bin/sh", "-c", fmt.Sprintf("zoofs node config  -E %s", export))

	w := bytes.NewBuffer(nil)
	cmd.Stderr = w
	cmd.Stdout = w
	if err := cmd.Run(); err != nil {
		fmt.Println(err)
	}
	yaml.Unmarshal([]byte(w.Bytes()), &config)
	exp := fmt.Sprintf("NODE: %s", export)
	nodes := config[exp]
	if len(nodes) == 0 {
	}
	//var volumes                                          TODO when a lot of vols
	var clusters []map[string][]map[string]string
	var clus []ConfigCluster
	fmt.Printf("configs:%+v\n", config)
	for _, node := range nodes {
		if volumes, ok := node["EXPORTD"]; ok {
			if vols, ok := volumes[0]["VOLUME"]; ok {
				for _, vol := range vols {
					if cs, ok := vol["volume 1"]; ok { //!!!!!!!!!!!volume 1
						clusters = cs
					}
				}
			}
		}
	}

	for _, cluster := range clusters {
		var clu ConfigCluster
		if ds, ok := cluster["cluster 1"]; ok { //!!!!!!!!!!!cluster 1
			clu.Cid = 1
			for _, dev := range ds {
				var node ConfigStorage
				for k, v := range dev {
					node.Sid, _ = strconv.Atoi(strings.Replace(k, "sid ", "", -1))
					node.Ip = v
					clu.Storages = append(clu.Storages, node)
				}
			}
		}
		clus = append(clus, clu)
	}
	return clus, nil
}

func rozoCmd(str string) (string, error) {
	cmd := exec.Command("/bin/sh", "-c", str)
	w := bytes.NewBuffer(nil)
	cmd.Stderr = w
	cmd.Stdout = w
	err := cmd.Run()
	return string(w.Bytes()), err
}

func errorCon(str string) bool {
	fails := []string{"FAILED", "usage", "failed"}

	for _, val := range fails {
		if strings.Index(str, val) >= 0 {
			return true
		}
	}
	return false
}
