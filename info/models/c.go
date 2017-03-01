package models

import (
	"fmt"
	"github.com/astaxie/beego/orm"
	"strconv"
)

type Mail struct {
	Id      int    `orm:"column(uid);auto"`
	Address string `orm:"column(address);size(64);null`
}

var (
	m map[string]map[string]int
)

func init() {
	orm.RegisterModel(new(Mail))
	m = make(map[string]map[string]int, 0)
}

func (s *Statistics) CheckStand() {
	o := orm.NewOrm()

	ones := make([]Machine, 0)
	if _, err := o.QueryTable(new(Machine)).Filter("status", true).All(&ones); err != nil {
		AddLog(err)
	}

	for _, val := range ones { //Get Machines
		if _, ok := m[val.Ip]; ok {
			continue
		} else {
			m[val.Ip] = map[string]int{ //TO DO  ip like "x.x.x.x"
				"cpu":   0,
				"mem":   0,
				"cache": 0,
			}
		}
	}

	if len(s.Exports) > 0 {
		for _, export := range s.Exports {
			if _, ok := m[export.Ip]; ok {
				Check(&export.Info[0], export.Ip)
			}
		}
	}
	if len(s.Storages) > 0 { //If machine exits
		for _, storage := range s.Storages {
			if _, ok := m[storage.Ip]; ok {
				Check(&storage.Info[0], storage.Ip)
			}
		}
	}

}

func Check(s *StoreView, ip string) {
	o := orm.NewOrm()
	count := 2
	//cpu
	if exist := o.QueryTable("threshhold").Filter("type", "cpu").Filter("warning__gt", s.Cpu).Exist(); !exist {
		m[ip]["cpu"] += 1
		if m[ip]["cpu"] == count {
			publish(ip, "cpu", s.Cpu)
		}
	} else {
		m[ip]["cpu"] = 0
	}
	//mem
	if exist := o.QueryTable("threshhold").Filter("type", "mem").Filter("warning__gt", s.Mem).Exist(); !exist {
		m[ip]["mem"] += 1
		if m[ip]["mem"] == count {
			publish(ip, "mem", s.Mem)
		}
	} else {
		m[ip]["mem"] = 0
	}
	//cache raid 1
	if exist := o.QueryTable("threshhold").Filter("type", "cache").Filter("warning__gt", s.CacheU).Exist(); !exist {
		m[ip]["cache"] += 1
		if m[ip]["cache"] == count {
			publish(ip, "cache", s.CacheU)
		}
	} else {
		m[ip]["cache"] = 0

	}
	for _, df := range s.Dfs {
		if df.Name == "system" {
			//system's cap
			if exist := o.QueryTable("threshhold").Filter("type", "systemCap").Filter("warning__gt", df.Used_per).Exist(); !exist {
				m[ip]["sysCap"] += 1
				if m[ip]["sysCap"] == count {
					publish(ip, "sysCap", df.Used_per)
				}
			} else {
				m[ip]["sysCap"] = 0
			}
		} else if df.Name == "filesystem" {
			//filesystem's cap
			if exist := o.QueryTable("threshhold").Filter("type", "filesystemCap").Filter("warning__gt", df.Used_per).Exist(); !exist {
				m[ip]["filesystemCap"] += 1
				if m[ip]["filesystemCap"] == count {
					publish(ip, "filesystemCap", df.Used_per)
				}
			} else {
				m[ip]["filesystemCap"] = 0
			}

			//special for yan
			//docker
		} else if df.Name == "docker" {
			if exist := o.QueryTable("threshhold").Filter("type", "dockerCap").Filter("warning__gt", df.Used_per).Exist(); !exist {
				m[ip]["dockerCap"] += 1
				if m[ip]["dockerCap"] == count {
					publish(ip, "dockerCap", df.Used_per)
				}
			} else {
				m[ip]["dockerCap"] = 0
			}
			//tmp
		} else if df.Name == "tmp" {
			if exist := o.QueryTable("threshhold").Filter("type", "tmpCap").Filter("warning__gt", df.Used_per).Exist(); !exist {
				m[ip]["tmpCap"] += 1
				if m[ip]["tmpCap"] == count {
					publish(ip, "tmpCap", df.Used_per)
				}
			} else {
				m[ip]["tmpCap"] = 0
			}
			//var for /var/log
		} else if df.Name == "var" {
			if exist := o.QueryTable("threshhold").Filter("type", "varCap").Filter("warning__gt", df.Used_per).Exist(); !exist {
				m[ip]["varCap"] += 1
				if m[ip]["varCap"] == count {
					publish(ip, "varCap", df.Used_per)
				}
			} else {
				m[ip]["varCap"] = 0
			}
			// weed_mem
		} else if df.Name == "weed_mem" {
			if exist := o.QueryTable("threshhold").Filter("type", "weedMem").Filter("warning__gt", df.Used_per).Exist(); !exist {
				m[ip]["weedMem"] += 1
				if m[ip]["weedMem"] == count {
					publish(ip, "weedMem", df.Used_per)
				}
			} else {
				m[ip]["weedMem"] = 0
			}
			// weed_cpu
		} else if df.Name == "weed_cpu" {
			if exist := o.QueryTable("threshhold").Filter("type", "weedCpu").Filter("warning__gt", df.Used_per).Exist(); !exist {
				m[ip]["weedCpu"] += 1
				if m[ip]["weedCpu"] == count {
					publish(ip, "weedCpu", df.Used_per)
				}
			} else {
				m[ip]["weedCpu"] = 0
			}
		}
	}

}

func publish(ip, typeVal string, val float64) {
	var message string
	if typeVal == "cpu" {
		message = "CPU超过阈值：" + strconv.FormatFloat(val, 'f', 1, 64)
	} else if typeVal == "mem" {
		message = "内存超过阈值：" + strconv.FormatFloat(val, 'f', 1, 64)
	} else if typeVal == "cache" {
		message = "阵列缓存超过阈值：" + strconv.FormatFloat(val, 'f', 1, 64)
	} else if typeVal == "sysCap" {
		message = "系统盘容量超过阈值：" + strconv.FormatFloat(val, 'f', 1, 64)
	} else if typeVal == "filesystemCap" {
		message = "文件系统容量超过阈值：" + strconv.FormatFloat(val, 'f', 1, 64)
	} else if typeVal == "dockerCap" {
		message = "docker文件夹超过阈值：" + strconv.FormatFloat(val, 'f', 1, 64)
	} else if typeVal == "tmpCap" {
		message = "tmp文件夹超过阈值：" + strconv.FormatFloat(val, 'f', 1, 64)
	} else if typeVal == "varCap" {
		message = "日志区var超过阈值：" + strconv.FormatFloat(val, 'f', 1, 64)
	} else if typeVal == "weedMem" {
		message = "minio_weed内存超过阈值：" + strconv.FormatFloat(val, 'f', 1, 64)
	} else if typeVal == "weedCpu" {
		message = "minio_weed CPU超过阈值：" + strconv.FormatFloat(val, 'f', 1, 64)
	}
	mail(ip + " " + message)
}

func mail(message string) {
	o := orm.NewOrm()
	var adds []Mail
	mails := make([]string, 0)
	if _, err := o.QueryTable("mail").All(&adds); err != nil {
		AddLog(err)
	}
	for _, val := range adds {
		mails = append(mails, val.Address)
	}
	MailSending(mails, message)
	fmt.Println(message)
}
