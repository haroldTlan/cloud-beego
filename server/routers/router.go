// @APIVersion 1.0.0
// @Title beego Test API
// @Description beego has a very cool tools to autogenerate documents for your API
// @Contact astaxie@gmail.com
// @TermsOfServiceUrl http://beego.me/
// @License Apache 2.0
// @LicenseUrl http://www.apache.org/licenses/LICENSE-2.0.html
package routers

import (
	"aserver/controllers"
	"aserver/controllers/device"
	"aserver/controllers/login"

	"github.com/astaxie/beego"
)

func init() {
	ns := beego.NewNamespace("/api",

		beego.NSNamespace("/sessions",
			beego.NSInclude(
				&login.LoginController{},
			),
		),

		beego.NSNamespace("/ifaces",
			beego.NSInclude(
				&login.LoginController{},
			),
		),
		beego.NSNamespace("/systeminfo",
			beego.NSInclude(
				&login.SystemInfoController{},
			),
		),
		beego.NSNamespace("/devices",
			beego.NSInclude(
				&device.DeviceController{},
			),
		),

		beego.NSNamespace("/storeviews",
			beego.NSInclude(
				&device.StoreViewsController{},
			),
		),
		beego.NSNamespace("/machines",
			beego.NSInclude(
				&controllers.MachineController{},
			),
		),
		beego.NSNamespace("/machinedetails",
			beego.NSInclude(
				&controllers.MachineDetailsController{},
			),
		),
		beego.NSNamespace("/journals",
			beego.NSInclude(
				&controllers.JournalsController{},
			),
		),
		/*	beego.NSNamespace("/client",
			beego.NSInclude(
				&controllers.ClientController{},
			),
		),*/
		beego.NSNamespace("/emergency",
			beego.NSInclude(
				&controllers.EmergencyController{},
			),
		),
		beego.NSNamespace("/threshhold",
			beego.NSInclude(
				&controllers.ThreshholdController{},
			),
		),
		beego.NSNamespace("/mail",
			beego.NSInclude(
				&controllers.MailController{},
			),
		),
		beego.NSNamespace("/zoofs",
			beego.NSInclude(
				&controllers.ZoofsController{},
			),
		),
		/*
			beego.NSNamespace("/emergency",
				beego.NSInclude(
					&controllers.EmergencyController{},
				),
			),

			beego.NSNamespace("/export",
				beego.NSInclude(
					&controllers.ExportController{},
				),
			),

			beego.NSNamespace("/journal",
				beego.NSInclude(
					&controllers.JournalController{},
				),
			),

			beego.NSNamespace("/journals",
				beego.NSInclude(
					&controllers.JournalsController{},
				),
			),

			beego.NSNamespace("/machines",
				beego.NSInclude(
					&controllers.MachineController{},
				),
			),

			beego.NSNamespace("/mail",
				beego.NSInclude(
					&controllers.MailController{},
				),
			),

			beego.NSNamespace("/storage",
				beego.NSInclude(
					&controllers.StorageController{},
				),
			),

			beego.NSNamespace("/threshhold",
				beego.NSInclude(
					&controllers.ThreshholdController{},
				),
			),*/
	)
	beego.AddNamespace(ns)
}
