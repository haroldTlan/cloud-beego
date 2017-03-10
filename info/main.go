package main

import (
	"beego_info/controllers"
	"beego_info/models"
	"github.com/astaxie/beego"
	"github.com/astaxie/beego/logs"
	"github.com/astaxie/beego/orm"
	_ "github.com/go-sql-driver/mysql"
)

func init() {
	orm.RegisterDataBase("default", "mysql", "root:passwd@tcp(127.0.0.1:3306)/speediodb?charset=utf8&loc=Local")
	logs.SetLogger(logs.AdapterFile, `{"filename":"info.log","daily":false,"maxdays":365,"level":3}`)
	logs.EnableFuncCallDepth(true)
	logs.Async()
}

func main() {
	//Must init first
	models.Ansible()
	models.InfoStat()

	beego.Router("/ws/info", &controllers.WebSocketController{}, "get:Join")
	if beego.BConfig.RunMode == "dev" {
		beego.BConfig.WebConfig.DirectoryIndex = true
		beego.BConfig.WebConfig.StaticDir["/swagger"] = "swagger"
	}
	beego.Run()
}
