package main

import (
	"flag"

	"aserver/models"
	"aserver/models/nsq"
	_ "aserver/routers"

	"github.com/astaxie/beego"
	"github.com/astaxie/beego/logs"
	"github.com/astaxie/beego/orm"
	_ "github.com/go-sql-driver/mysql"
)

var (
	nsq_ip      = beego.AppConfig.String("nsq") + ":" + beego.AppConfig.String("nsq_pub_port")
	nsqdAddr    = flag.String("nsqd", nsq_ip, "nsqd http address")
	maxInFlight = flag.Int("max-in-flight", 200, "Maximum amount of messages in flight to consume")
)

func init() {
	orm.RegisterDataBase("default", "mysql", "root:passwd@tcp(127.0.0.1:3306)/speediodb?charset=utf8&loc=Local")

	logs.SetLogger(logs.AdapterFile, `{"filename":"/var/log/zoofsmonitor.log","daily":false,"maxdays":365,"level":3}`)
	logs.EnableFuncCallDepth(true)
	logs.Async()

}

func main() {
	nsq.NsqInit()
	models.Outline()
	models.Online()
	if beego.BConfig.RunMode == "dev" {
		beego.BConfig.WebConfig.DirectoryIndex = true
		beego.BConfig.WebConfig.StaticDir["/swagger"] = "swagger"
	}
	beego.Run()
}
