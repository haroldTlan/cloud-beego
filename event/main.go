package main

import (
	"flag"

	"event/controllers"
	"event/models/nsq"
	"github.com/astaxie/beego"
	"github.com/astaxie/beego/logs"
	"github.com/astaxie/beego/orm"
	_ "github.com/go-sql-driver/mysql"
)

var (
	nsq_ip       = beego.AppConfig.String("nsq") + ":" + beego.AppConfig.String("nsq_port")
	nsqdAddr     = flag.String("nsqd", nsq_ip, "nsqd http address")
	maxInFlight  = flag.Int("max-in-flight", 200, "Maximum amount of messages in flight to consume")
	registerIp   = beego.AppConfig.String("registerDB")
	registerPort = beego.AppConfig.String("registerPort")
)

func init() {
	orm.RegisterDataBase("default", "mysql", "root:passwd@tcp("+registerIp+":"+registerPort+")/speediodb?charset=utf8&loc=Local")

	//setting log, type event
	logs.SetLogger(logs.AdapterFile, `{"filename":"/var/log/zoofsmonitor.log","daily":false,"maxdays":365,"level":3}`)
	logs.EnableFuncCallDepth(true)
	logs.Async()
}

func main() {
	flag.Parse()

	//init nsq and get events from pubs
	go nsq.RunConsumer(*maxInFlight, *nsqdAddr)

	beego.Router("/ws/event", &controllers.WebSocketController{}, "get:Join")

	if beego.BConfig.RunMode == "dev" {
		beego.BConfig.WebConfig.DirectoryIndex = true
		beego.BConfig.WebConfig.StaticDir["/swagger"] = "swagger"
	}
	beego.Run()
}
