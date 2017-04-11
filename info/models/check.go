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

//use ansible to get devices infomations then check
func (s *Statistics) CheckStand() {
	o := orm.NewOrm()

	ones := make([]Machine, 0)
	if _, err := o.QueryTable(new(Machine)).Filter("status", true).All(&ones); err != nil {
		AddLog(err)
	}

	for _, val := range ones { //Get Machines
		if _, ok := m[val.Ip]; ok { //if ip has been init, then continue
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
				Check(&export.Info[0], export.Ip, "export")
			}
		}
	}
	if len(s.Storages) > 0 { //If machine exits
		for _, storage := range s.Storages {
			if _, ok := m[storage.Ip]; ok {
				Check(&storage.Info[0], storage.Ip, "storage")
			}
		}
	}

}

func Check(s *StoreView, ip, devtype string) {
	o := orm.NewOrm()
	count := 5
	//cpu
	if exist := o.QueryTable("threshhold").Filter("type", devtype).Filter("dev", "cpu").Filter("warning__lt", s.Cpu).Exist(); exist {
		m[ip]["cpu"] += 1
		if m[ip]["cpu"] == count {
			publish(ip, "cpu", s.Cpu)
		}
	} else {
		m[ip]["cpu"] = 0
	}
	//mem
	if exist := o.QueryTable("threshhold").Filter("type", devtype).Filter("dev", "mem").Filter("warning__lt", s.Mem).Exist(); exist {
		m[ip]["mem"] += 1
		if m[ip]["mem"] == count {
			publish(ip, "mem", s.Mem, s.MemT)
		}
	} else {
		m[ip]["mem"] = 0
	}
	//cache raid 1
	if exist := o.QueryTable("threshhold").Filter("type", devtype).Filter("dev", "cache").Filter("warning__lt", s.CacheU/s.CacheT).Exist(); exist {
		m[ip]["cache"] += 1
		if m[ip]["cache"] == count {
			publish(ip, "cache", s.CacheU/s.CacheT)
		}
	} else {
		m[ip]["cache"] = 0

	}
	for _, df := range s.Dfs {
		if df.Name == "system" {
			//system's cap
			if exist := o.QueryTable("threshhold").Filter("type", devtype).Filter("dev", "systemCap").Filter("warning__lt", df.Used_per).Exist(); exist {
				m[ip]["sysCap"] += 1
				if m[ip]["sysCap"] == count {
					publish(ip, "sysCap", df.Used_per)
				}
			} else {
				m[ip]["sysCap"] = 0
			}
		} else if df.Name == "filesystem" {
			//filesystem's cap
			if exist := o.QueryTable("threshhold").Filter("type", devtype).Filter("dev", "filesystemCap").Filter("warning__lt", df.Used_per).Exist(); exist {
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
			if exist := o.QueryTable("threshhold").Filter("type", devtype).Filter("dev", "dockerCap").Filter("warning__lt", df.Used_per).Exist(); exist {
				m[ip]["dockerCap"] += 1
				if m[ip]["dockerCap"] == count {
					publish(ip, "dockerCap", df.Used_per)
				}
			} else {
				m[ip]["dockerCap"] = 0
			}
			//tmp
		} else if df.Name == "tmp" {
			if exist := o.QueryTable("threshhold").Filter("type", devtype).Filter("dev", "tmpCap").Filter("warning__lt", df.Used_per).Exist(); exist {
				m[ip]["tmpCap"] += 1
				if m[ip]["tmpCap"] == count {
					publish(ip, "tmpCap", df.Used_per)
				}
			} else {
				m[ip]["tmpCap"] = 0
			}
			//var for /var/log
		} else if df.Name == "var" {
			if exist := o.QueryTable("threshhold").Filter("type", devtype).Filter("dev", "varCap").Filter("warning__lt", df.Used_per).Exist(); exist {
				m[ip]["varCap"] += 1
				if m[ip]["varCap"] == count {
					publish(ip, "varCap", df.Used_per)
				}
			} else {
				m[ip]["varCap"] = 0
			}
			// weed_mem
		} else if df.Name == "weed_mem" {
			if exist := o.QueryTable("threshhold").Filter("type", devtype).Filter("dev", "weedMem").Filter("warning__lt", df.Used_per).Exist(); exist {
				m[ip]["weedMem"] += 1
				if m[ip]["weedMem"] == count {
					publish(ip, "weedMem", df.Used_per, s.MemT, df.Available)
				}
			} else {
				m[ip]["weedMem"] = 0
			}
			// weed_cpu
		} else if df.Name == "weed_cpu" {
			if exist := o.QueryTable("threshhold").Filter("type", devtype).Filter("dev", "weedCpu").Filter("warning__lt", df.Used_per).Exist(); exist {
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

func publish(ip, typeVal string, val float64, d ...float64) {
	var message string
	if typeVal == "cpu" {
		message = "CPU超过阈值：" + strconv.FormatFloat(val, 'f', 1, 64) + "%/100%"
	} else if typeVal == "mem" {
		t := strconv.FormatFloat(d[0]/1024/1024/1024, 'f', 1, 64)
		tMb := strconv.FormatFloat(d[0]/1024/1024, 'f', 1, 64)
		u := strconv.FormatFloat(d[0]/1024/1024/1024*val/100, 'f', 1, 64)
		uMb := strconv.FormatFloat(d[0]/1024/1024*val/100, 'f', 1, 64)
		f := strconv.FormatFloat(d[0]/1024/1024/1024*(1-val/100), 'f', 1, 64)
		fMb := strconv.FormatFloat(d[0]/1024/1024*(1-val/100), 'f', 1, 64)
		message = "内存超过阈值：" + strconv.FormatFloat(val, 'f', 1, 64) + "%/100%" + "<br>" +
			"Total: " + t + "G(" + tMb + "M)" + "<br>" +
			"Used: " + u + "G(" + uMb + "M)" + "<br>" +
			"Free(含cache): " + f + "G(" + fMb + "M)"

	} else if typeVal == "cache" {
		message = "阵列缓存超过阈值：" + strconv.FormatFloat(val, 'f', 1, 64) + "%/100%"
	} else if typeVal == "sysCap" {
		message = "系统盘容量超过阈值：" + strconv.FormatFloat(val, 'f', 1, 64) + "%/100%"
	} else if typeVal == "filesystemCap" {
		message = "文件系统容量超过阈值：" + strconv.FormatFloat(val, 'f', 1, 64) + "%/100%"
	} else if typeVal == "dockerCap" {
		message = "docker文件夹超过阈值：" + strconv.FormatFloat(val, 'f', 1, 64) + "%/100%"
	} else if typeVal == "tmpCap" {
		message = "tmp文件夹超过阈值：" + strconv.FormatFloat(val, 'f', 1, 64) + "%/100%"
	} else if typeVal == "varCap" {
		message = "日志区var超过阈值：" + strconv.FormatFloat(val, 'f', 1, 64) + "%/100%"
	} else if typeVal == "weedMem" {
		t := strconv.FormatFloat(d[0]/1024/1024/1024, 'f', 1, 64)
		tMb := strconv.FormatFloat(d[0]/1024/1024, 'f', 1, 64)
		u := strconv.FormatFloat(d[0]/1024/1024/1024*val/100, 'f', 1, 64)
		uMb := strconv.FormatFloat(d[0]/1024/1024*val/100, 'f', 1, 64)
		f := strconv.FormatFloat(d[0]/1024/1024/1024*(1-d[1]/100), 'f', 1, 64)
		fMb := strconv.FormatFloat(d[0]/1024/1024*(1-d[1]/100), 'f', 1, 64)
		message = "minio内存超过阈值：" + strconv.FormatFloat(val, 'f', 1, 64) + "%/100%" + "<br>" +
			"Total: " + t + "G(" + tMb + "M)" + "<br>" +
			"Used: " + u + "G(" + uMb + "M)" + "<br>" +
			"Free(含cache): " + f + "G(" + fMb + "M)"

	} else if typeVal == "weedCpu" {
		message = "minio CPU超过阈值：" + strconv.FormatFloat(val*8, 'f', 1, 64) + "%/800%"
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
