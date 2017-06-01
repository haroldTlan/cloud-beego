package models

import (
	"github.com/astaxie/beego"
	"gopkg.in/gomail.v2"
	"time"

	"encoding/json"
	"os"
)

func init() {
	MailDaemon()
}

var ChOfMail = make(chan *gomail.Message)

func MailSending(to []string, message string) {
	header := beego.AppConfig.String("mailHeader")

	m := gomail.NewMessage()
	m.SetHeader("From", "public@zexabox.com")
	m.SetHeader("To", to...)
	m.SetHeader("Subject", header)
	m.SetBody("text/html", message)
	ChOfMail <- m
}

func MailDaemon() {
	go func() {
		from := "public@zexabox.com"
		password := "Zexapub123"
		d := gomail.NewDialer("smtp.exmail.qq.com", 25, from, password)
		var err error
		var s gomail.SendCloser
		open := false
		for {
			select {
			case m, ok := <-ChOfMail:
				if !ok {
					return
				}
				if !open {
					if s, err = d.Dial(); err != nil {
						AddLog(err)
						for i := 0; i < 3; i++ {
							if s, err = d.Dial(); err != nil {
								AddLog(err)
								time.Sleep(2 * time.Second)
								continue
							} else {
								AddLog("Dial Success!!")
								break
							}
						}
					}
					if err == nil {
						open = true
					}

				}
				if s != nil {
					if err := gomail.Send(s, m); err != nil {
						AddLog(err)
					}
				}
			case <-time.After(30 * time.Second):
				if open {
					if err := s.Close(); err != nil {
						AddLog(err, "smtp close: ")
					}
					AddLog("smtp close")
					open = false
				}
			}
		}
	}()
}

func WriteConf(path string, yaml []byte) {
	//yaml := []byte(str)

	fi, err := os.OpenFile(path, os.O_WRONLY|os.O_APPEND, 0666)
	if err != nil {
		panic(err)
	}
	defer fi.Close()

	//err = ioutil.WriteFile(path, yaml, 0666)
	res := append(yaml)
	if _, err = fi.Write(res); err != nil {
		panic(err)
	}

}

func DrawSetting(i StoreView) {
	var d Drawing

	d.Ip = i.Ip
	d.Dev = i.Dev
	d.Write = i.Write
	d.Read = i.Read
	d.TimeStamp = i.TimeStamp
	d.CacheT = i.CacheT
	d.CacheU = i.CacheU
	d.W_Vol = i.W_Vol
	d.R_Vol = i.R_Vol

	for _, i := range i.Dfs {
		if i.Name == "tmp" {
			d.Tmp = i.Used_per
		} else if i.Name == "system" {
			d.System = i.Used_per
		} else if i.Name == "weed_cpu" {
			d.WeedCpu = i.Used_per
		} else if i.Name == "weed_mem" {
			d.WeedMem = i.Used_per
		} else if i.Name == "var" {
			d.Var = i.Used_per
		}

	}

	first, _ := json.Marshal(d)
	path := beego.AppConfig.String("drawing")
	WriteConf(path, append(first, []byte("\n")...))
}
