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
	"aserver/controllers/ansible"
	"aserver/controllers/device"
	"aserver/controllers/login"

	"github.com/astaxie/beego"
)

func init() {
	ns := beego.NewNamespace("/api",

		//can be deleted or TODO
		beego.NSNamespace("/sessions",
			beego.NSInclude(
				&login.LoginController{},
			),
		),

		//network interface
		beego.NSNamespace("/ifaces",
			beego.NSInclude(
				&login.IfaceController{},
			),
		),

		//can be deleted or TODO
		beego.NSNamespace("/systeminfo",
			beego.NSInclude(
				&login.SystemInfoController{},
			),
		),

		//include storage, export, client
		beego.NSNamespace("/devices",
			beego.NSInclude(
				&device.DeviceController{},
			),
		),

		//overviews information
		beego.NSNamespace("/storeviews",
			beego.NSInclude(
				&device.StoreViewsController{},
			),
		),

		//monitored machine
		beego.NSNamespace("/machines",
			beego.NSInclude(
				&controllers.MachineController{},
			),
		),

		//All machine's detail
		//不应该这样做，一次性拿所有的detail推到前台，是个很傻帽的做法
		//无奈前端是sb, me too, 不想说了
		beego.NSNamespace("/machinedetails",
			beego.NSInclude(
				&controllers.MachineDetailsController{},
			),
		),

		//local journals, just emergency, TODO  setting journals
		beego.NSNamespace("/journals",
			beego.NSInclude(
				&controllers.JournalsController{},
			),
		),

		//client's setting, like create, remove
		beego.NSNamespace("/client",
			beego.NSInclude(
				&controllers.ClientController{},
			),
		),

		//emergency's setting, like
		beego.NSNamespace("/emergency",
			beego.NSInclude(
				&controllers.EmergencyController{},
			),
		),

		//--------------------------------------->
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
		beego.NSNamespace("/storage",
			beego.NSInclude(
				&controllers.StorageController{},
			),
		),
		beego.NSNamespace("/cluster",
			beego.NSInclude(
				&controllers.ClustersController{},
			),
		),
		beego.NSNamespace("/ansible",
			beego.NSInclude(
				&ansible.AnsibleController{},
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



			beego.NSNamespace("/threshhold",
				beego.NSInclude(
					&controllers.ThreshholdController{},
				),
			),*/
	)
	beego.AddNamespace(ns)
}
