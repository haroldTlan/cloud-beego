package main

import (
	"beego_info/controllers"

	"beego_info/models"
	"github.com/astaxie/beego"
	"github.com/astaxie/beego/orm"
	_ "github.com/go-sql-driver/mysql"
	//	"time"
)

func init() {
	orm.RegisterDataBase("default", "mysql", "root:passwd@tcp(127.0.0.1:3306)/speediodb?charset=utf8&loc=Local")

	/*	go func() {
		for {
			fmt.Println("??", info.ResolveConf())
			a := info.ResolveConf()
			controllers.StatTopic.Publish(a)

			time.Sleep(2 * time.Second)
		}
	}()*/
}

func main() {
	models.Ansible()
	models.InfoStat()
	beego.Router("/ws/join", &controllers.WebSocketController{}, "get:Join")
	if beego.BConfig.RunMode == "dev" {
		beego.BConfig.WebConfig.DirectoryIndex = true
		beego.BConfig.WebConfig.StaticDir["/swagger"] = "swagger"
	}
	beego.Run()

}
