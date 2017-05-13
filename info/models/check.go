package models

import (
	_ "fmt"
	"github.com/astaxie/beego/orm"
	"strconv"
)

type Mail struct {
	Id      int    `orm:"column(uid);auto"`
	Address string `orm:"column(address);size(64);null`
}

var (
	m map[string]map[string]map[string]int
)

func init() {
	orm.RegisterModel(new(Mail))
	m = make(map[string]map[string]map[string]int, 0)
}

//use ansible to get devices infomations then check
func (s *Statistics) CheckStand() {
	o := orm.NewOrm()

	ones := make([]Machine, 0)
	if _, err := o.QueryTable(new(Machine)).Filter("status", true).All(&ones); err != nil {
		AddLog(err)
	}

	for _, val := range ones { //Get Machines
		if _, ok := m[val.Ip][val.Devtype]; ok { //if ip has been init, then continue
			continue
		} else {
			if len(m[val.Ip]) > 0 {
				m[val.Ip][val.Devtype] = map[string]int{ //TO DO  ip like "x.x.x.x"
					"cpu":   0,
					"mem":   0,
					"cache": 0,
				}
			} else {
				typeMap := make(map[string]map[string]int)
				typeMap[val.Devtype] = map[string]int{ //TO DO  ip like "x.x.x.x"
					"cpu":   0,
					"mem":   0,
					"cache": 0,
				}
				m[val.Ip] = typeMap
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
	var thresh Threshhold
	o := orm.NewOrm()
	count := 3 //number of inspections

	//cpu
	cpu := "cpu"
	if exist := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", cpu).Filter("warning__lt", s.Cpu).Exist(); exist {
		m[ip][devtype][cpu] += 1
		if m[ip][devtype][cpu] == count {
			//Get Warning
			err := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", cpu).One(&thresh)
			if err != nil {
				AddLog(err)
			}

			publish(ip, cpu, devtype, s.Cpu, thresh.Warning)
		}
	} else {
		m[ip][devtype][cpu] = 0
	}

	//mem
	mem := "mem"
	if exist := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", mem).Filter("warning__lt", s.Mem).Exist(); exist {
		m[ip][devtype][mem] += 1
		if m[ip][devtype][mem] == count {
			//Get Warning
			err := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", mem).One(&thresh)
			if err != nil {
				AddLog(err)
			}
			publish(ip, mem, devtype, s.Mem, thresh.Warning, s.MemT)
		}
	} else {
		m[ip][devtype][mem] = 0
	}

	//cache raid 1
	cache := "cache"
	if exist := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", cache).Filter("warning__lt", s.CacheU/s.CacheT).Exist(); exist {
		m[ip][devtype][cache] += 1
		if m[ip][devtype][cache] == count {
			//Get Warning
			err := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", cache).One(&thresh)
			if err != nil {
				AddLog(err)
			}

			publish(ip, cache, devtype, s.CacheU/s.CacheT, thresh.Warning)
		}
	} else {
		m[ip][devtype][cache] = 0
	}

	//Df
	for _, df := range s.Dfs {
		if df.Name == "system" {
			//system's cap
			sysCap := "systemCap"
			if exist := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", sysCap).Filter("warning__lt", df.Used_per).Exist(); exist {
				m[ip][devtype][sysCap] += 1
				if m[ip][devtype][sysCap] == count {
					//Get Warning
					err := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", sysCap).One(&thresh)
					if err != nil {
						AddLog(err)
					}

					publish(ip, sysCap, devtype, df.Used_per, thresh.Warning)
				}
			} else {
				m[ip][devtype][sysCap] = 0
			}

		} else if df.Name == "filesystem" {
			//filesystem's cap
			fsCap := "filesystemCap"
			if exist := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", fsCap).Filter("warning__lt", df.Used_per).Exist(); exist {
				m[ip][devtype][fsCap] += 1
				if m[ip][devtype][fsCap] == count {
					//Get Warning
					err := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", fsCap).One(&thresh)
					if err != nil {
						AddLog(err)
					}

					publish(ip, fsCap, devtype, df.Used_per, thresh.Warning)
				}
			} else {
				m[ip][devtype][fsCap] = 0
			}

			//special for yan
			//docker
		} else if df.Name == "docker" {
			dockerCap := "dockerCap"
			if exist := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", dockerCap).Filter("warning__lt", df.Used_per).Exist(); exist {
				m[ip][devtype][dockerCap] += 1
				if m[ip][devtype][dockerCap] == count {
					//Get Warning
					err := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", dockerCap).One(&thresh)
					if err != nil {
						AddLog(err)
					}

					publish(ip, dockerCap, devtype, df.Used_per, thresh.Warning)
				}
			} else {
				m[ip][devtype][dockerCap] = 0
			}

			//tmp
		} else if df.Name == "tmp" {
			tmpCap := "tmpCap"
			if exist := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", tmpCap).Filter("warning__lt", df.Used_per).Exist(); exist {
				m[ip][devtype][tmpCap] += 1
				if m[ip][devtype][tmpCap] == count {
					//Get Warning
					err := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", tmpCap).One(&thresh)
					if err != nil {
						AddLog(err)
					}

					publish(ip, tmpCap, devtype, df.Used_per, thresh.Warning)
				}
			} else {
				m[ip][devtype][tmpCap] = 0
			}

			//var for /var/log
		} else if df.Name == "var" {
			varCap := "varCap"
			if exist := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", "varCap").Filter("warning__lt", df.Used_per).Exist(); exist {
				m[ip][devtype][varCap] += 1
				if m[ip][devtype][varCap] == count {
					//Get Warning
					err := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", varCap).One(&thresh)
					if err != nil {
						AddLog(err)
					}

					publish(ip, varCap, devtype, df.Used_per, thresh.Warning)
				}
			} else {
				m[ip][devtype][varCap] = 0
			}

			// weed_mem
		} else if df.Name == "weed_mem" {
			weedMem := "weedMem"
			if exist := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", weedMem).Filter("warning__lt", df.Used_per).Exist(); exist {
				m[ip][devtype][weedMem] += 1
				if m[ip][devtype][weedMem] == count {
					//Get Warning
					err := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", weedMem).One(&thresh)
					if err != nil {
						AddLog(err)
					}

					publish(ip, weedMem, devtype, df.Used_per, thresh.Warning, s.MemT, df.Available)
				}
			} else {
				m[ip][devtype][weedMem] = 0
			}

			// weed_cpu
		} else if df.Name == "weed_cpu" {
			weedCpu := "weedCpu"
			if exist := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", weedCpu).Filter("warning__lt", df.Used_per).Exist(); exist {
				m[ip][devtype][weedCpu] += 1
				if m[ip][devtype][weedCpu] == count {
					//Get Warning
					err := o.QueryTable(new(Threshhold)).Filter("type", devtype).Filter("dev", weedCpu).One(&thresh)
					if err != nil {
						AddLog(err)
					}

					publish(ip, weedCpu, devtype, df.Used_per, thresh.Warning)
				}
			} else {
				m[ip][devtype][weedCpu] = 0
			}
		}
	}
}

func publish(ip, typeVal, devtype string, val, warning float64, d ...float64) {
	var message string

	if typeVal == "cpu" {
		message = "CPU超过阈值(" + strconv.FormatFloat(warning, 'f', 1, 64) + "%)：" + strconv.FormatFloat(val, 'f', 1, 64) + "%/100%"
	} else if typeVal == "mem" {
		t := strconv.FormatFloat(d[0]/1024/1024/1024, 'f', 1, 64)
		tMb := strconv.FormatFloat(d[0]/1024/1024, 'f', 1, 64)
		u := strconv.FormatFloat(d[0]/1024/1024/1024*val/100, 'f', 1, 64)
		uMb := strconv.FormatFloat(d[0]/1024/1024*val/100, 'f', 1, 64)
		f := strconv.FormatFloat(d[0]/1024/1024/1024*(1-val/100), 'f', 1, 64)
		fMb := strconv.FormatFloat(d[0]/1024/1024*(1-val/100), 'f', 1, 64)
		message = "内存超过阈值(" + strconv.FormatFloat(warning, 'f', 1, 64) + "%)：" + strconv.FormatFloat(val, 'f', 1, 64) + "%/100%" + "<br>" +
			"Total: " + t + "G(" + tMb + "M)" + "<br>" +
			"Used: " + u + "G(" + uMb + "M)" + "<br>" +
			"Free(含cache): " + f + "G(" + fMb + "M)"

	} else if typeVal == "cache" {
		message = "阵列缓存超过阈值(" + strconv.FormatFloat(warning, 'f', 1, 64) + "%)：" + strconv.FormatFloat(val, 'f', 1, 64) + "%/100%"
	} else if typeVal == "systemCap" {
		message = "系统盘容量超过阈值(" + strconv.FormatFloat(warning, 'f', 1, 64) + "%)：" + strconv.FormatFloat(val, 'f', 1, 64) + "%/100%"
	} else if typeVal == "filesystemCap" {
		message = "文件系统容量超过阈值(" + strconv.FormatFloat(warning, 'f', 1, 64) + "%)：" + strconv.FormatFloat(val, 'f', 1, 64) + "%/100%"
	} else if typeVal == "dockerCap" {
		message = "docker文件夹超过阈值(" + strconv.FormatFloat(warning, 'f', 1, 64) + "%)：" + strconv.FormatFloat(val, 'f', 1, 64) + "%/100%"
	} else if typeVal == "tmpCap" {
		message = "tmp文件夹超过阈值(" + strconv.FormatFloat(warning, 'f', 1, 64) + "%)：" + strconv.FormatFloat(val, 'f', 1, 64) + "%/100%"
	} else if typeVal == "varCap" {
		message = "日志区var超过阈值(" + strconv.FormatFloat(warning, 'f', 1, 64) + "%)：" + strconv.FormatFloat(val, 'f', 1, 64) + "%/100%"
	} else if typeVal == "weedMem" {
		t := strconv.FormatFloat(d[0]/1024/1024/1024, 'f', 1, 64)
		tMb := strconv.FormatFloat(d[0]/1024/1024, 'f', 1, 64)
		u := strconv.FormatFloat(d[0]/1024/1024/1024*val/100, 'f', 1, 64)
		uMb := strconv.FormatFloat(d[0]/1024/1024*val/100, 'f', 1, 64)
		f := strconv.FormatFloat(d[0]/1024/1024/1024*(1-d[1]/100), 'f', 1, 64)
		fMb := strconv.FormatFloat(d[0]/1024/1024*(1-d[1]/100), 'f', 1, 64)
		if devtype == "export" {
			message = "minio内存超过阈值(" + strconv.FormatFloat(warning, 'f', 1, 64) + "%)：" + strconv.FormatFloat(val, 'f', 1, 64) + "%/100%" + "<br>" +
				"Total: " + t + "G(" + tMb + "M)" + "<br>" +
				"Used: " + u + "G(" + uMb + "M)" + "<br>" +
				"Free(含cache): " + f + "G(" + fMb + "M)"
		} else {
			message = "weed内存超过阈值(" + strconv.FormatFloat(warning, 'f', 1, 64) + "%)：" + strconv.FormatFloat(val, 'f', 1, 64) + "%/100%" + "<br>" +
				"Total: " + t + "G(" + tMb + "M)" + "<br>" +
				"Used: " + u + "G(" + uMb + "M)" + "<br>" +
				"Free(含cache): " + f + "G(" + fMb + "M)"

		}

	} else if typeVal == "weedCpu" {
		message = "minio CPU超过阈值(" + strconv.FormatFloat(warning, 'f', 1, 64) + "%)：" + strconv.FormatFloat(val*8, 'f', 1, 64) + "%/800%"
	}
	Mailing(ip + " " + message)
}

func Mailing(message string) {
	o := orm.NewOrm()

	AddLog(message)
	var adds []Mail
	mails := make([]string, 0)
	if _, err := o.QueryTable("mail").All(&adds); err != nil {
		AddLog(err)
	}
	for _, val := range adds {
		mails = append(mails, val.Address)
	}
	if len(mails) > 0 {
		MailSending(mails, message)
	}
}
