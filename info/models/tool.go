package models

import (
	"fmt"
	"github.com/astaxie/beego"
	"gopkg.in/gomail.v2"
	"time"
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
					fmt.Printf("%+v", d)
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

					open = true
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
