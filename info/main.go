package main

import (
	"flag"

	"beego_info/controllers"
	"beego_info/models"
	"github.com/astaxie/beego"
	"github.com/astaxie/beego/logs"
	"github.com/astaxie/beego/orm"
	_ "github.com/go-sql-driver/mysql"
)

var (
	nsq_ip      = beego.AppConfig.String("nsq") + ":" + beego.AppConfig.String("nsq_port")
	nsqdAddr    = flag.String("nsqd", nsq_ip, "nsqd http address")
	maxInFlight = flag.Int("max-in-flight", 200, "Maximum amount of messages in flight to consume")
)

func init() {
	orm.RegisterDataBase("default", "mysql", "root:passwd@tcp(127.0.0.1:3306)/speediodb?charset=utf8&loc=Local")

	//setting log, file in info's dir
	logs.SetLogger(logs.AdapterFile, `{"filename":"/var/log/zoofsmonitor.log","daily":false,"maxdays":365,"level":3}`)
	logs.EnableFuncCallDepth(true)
	logs.Async()
}

func main() {
	flag.Parse()
	//Must init first
	//checking infos from nsq
	go models.InfoStat()
	//init nsq and get infos from pubs
	go models.RunConsumer(*maxInFlight, *nsqdAddr)
	//clear global variable when datas did not found or machine did not being monitored.
	go models.ClearInfos()

	beego.Router("/ws/info", &controllers.WebSocketController{}, "get:Join")
	if beego.BConfig.RunMode == "dev" {
		beego.BConfig.WebConfig.DirectoryIndex = true
		beego.BConfig.WebConfig.StaticDir["/swagger"] = "swagger"
	}
	beego.Run()
}
