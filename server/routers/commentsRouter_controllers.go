package routers

import (
	"github.com/astaxie/beego"
)

func init() {

	beego.GlobalControllerRouter["aserver/controllers:ClientController"] = append(beego.GlobalControllerRouter["aserver/controllers:ClientController"],
		beego.ControllerComments{
			Method: "Post",
			Router: `/`,
			AllowHTTPMethods: []string{"post"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:ClientController"] = append(beego.GlobalControllerRouter["aserver/controllers:ClientController"],
		beego.ControllerComments{
			Method: "GetOne",
			Router: `/:id`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:ClientController"] = append(beego.GlobalControllerRouter["aserver/controllers:ClientController"],
		beego.ControllerComments{
			Method: "GetAll",
			Router: `/`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:ClientController"] = append(beego.GlobalControllerRouter["aserver/controllers:ClientController"],
		beego.ControllerComments{
			Method: "Put",
			Router: `/:id`,
			AllowHTTPMethods: []string{"put"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:ClientController"] = append(beego.GlobalControllerRouter["aserver/controllers:ClientController"],
		beego.ControllerComments{
			Method: "Delete",
			Router: `/:id`,
			AllowHTTPMethods: []string{"delete"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:EmergencyController"] = append(beego.GlobalControllerRouter["aserver/controllers:EmergencyController"],
		beego.ControllerComments{
			Method: "Post",
			Router: `/`,
			AllowHTTPMethods: []string{"post"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:EmergencyController"] = append(beego.GlobalControllerRouter["aserver/controllers:EmergencyController"],
		beego.ControllerComments{
			Method: "GetOne",
			Router: `/:id`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:EmergencyController"] = append(beego.GlobalControllerRouter["aserver/controllers:EmergencyController"],
		beego.ControllerComments{
			Method: "GetAll",
			Router: `/`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:EmergencyController"] = append(beego.GlobalControllerRouter["aserver/controllers:EmergencyController"],
		beego.ControllerComments{
			Method: "Put",
			Router: `/:id`,
			AllowHTTPMethods: []string{"put"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:EmergencyController"] = append(beego.GlobalControllerRouter["aserver/controllers:EmergencyController"],
		beego.ControllerComments{
			Method: "Delete",
			Router: `/:id`,
			AllowHTTPMethods: []string{"delete"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:ExportController"] = append(beego.GlobalControllerRouter["aserver/controllers:ExportController"],
		beego.ControllerComments{
			Method: "Post",
			Router: `/`,
			AllowHTTPMethods: []string{"post"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:ExportController"] = append(beego.GlobalControllerRouter["aserver/controllers:ExportController"],
		beego.ControllerComments{
			Method: "GetOne",
			Router: `/:id`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:ExportController"] = append(beego.GlobalControllerRouter["aserver/controllers:ExportController"],
		beego.ControllerComments{
			Method: "GetAll",
			Router: `/`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:ExportController"] = append(beego.GlobalControllerRouter["aserver/controllers:ExportController"],
		beego.ControllerComments{
			Method: "Put",
			Router: `/:id`,
			AllowHTTPMethods: []string{"put"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:ExportController"] = append(beego.GlobalControllerRouter["aserver/controllers:ExportController"],
		beego.ControllerComments{
			Method: "Delete",
			Router: `/:id`,
			AllowHTTPMethods: []string{"delete"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:JournalController"] = append(beego.GlobalControllerRouter["aserver/controllers:JournalController"],
		beego.ControllerComments{
			Method: "Post",
			Router: `/`,
			AllowHTTPMethods: []string{"post"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:JournalController"] = append(beego.GlobalControllerRouter["aserver/controllers:JournalController"],
		beego.ControllerComments{
			Method: "GetOne",
			Router: `/:id`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:JournalController"] = append(beego.GlobalControllerRouter["aserver/controllers:JournalController"],
		beego.ControllerComments{
			Method: "GetAll",
			Router: `/`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:JournalController"] = append(beego.GlobalControllerRouter["aserver/controllers:JournalController"],
		beego.ControllerComments{
			Method: "Put",
			Router: `/:id`,
			AllowHTTPMethods: []string{"put"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:JournalController"] = append(beego.GlobalControllerRouter["aserver/controllers:JournalController"],
		beego.ControllerComments{
			Method: "Delete",
			Router: `/:id`,
			AllowHTTPMethods: []string{"delete"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:JournalsController"] = append(beego.GlobalControllerRouter["aserver/controllers:JournalsController"],
		beego.ControllerComments{
			Method: "Post",
			Router: `/`,
			AllowHTTPMethods: []string{"post"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:JournalsController"] = append(beego.GlobalControllerRouter["aserver/controllers:JournalsController"],
		beego.ControllerComments{
			Method: "GetOne",
			Router: `/:id`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:JournalsController"] = append(beego.GlobalControllerRouter["aserver/controllers:JournalsController"],
		beego.ControllerComments{
			Method: "GetAll",
			Router: `/`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:JournalsController"] = append(beego.GlobalControllerRouter["aserver/controllers:JournalsController"],
		beego.ControllerComments{
			Method: "Put",
			Router: `/:id`,
			AllowHTTPMethods: []string{"put"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:JournalsController"] = append(beego.GlobalControllerRouter["aserver/controllers:JournalsController"],
		beego.ControllerComments{
			Method: "Delete",
			Router: `/:id`,
			AllowHTTPMethods: []string{"delete"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:MachineController"] = append(beego.GlobalControllerRouter["aserver/controllers:MachineController"],
		beego.ControllerComments{
			Method: "Post",
			Router: `/`,
			AllowHTTPMethods: []string{"post"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:MachineController"] = append(beego.GlobalControllerRouter["aserver/controllers:MachineController"],
		beego.ControllerComments{
			Method: "GetOne",
			Router: `/:id`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:MachineController"] = append(beego.GlobalControllerRouter["aserver/controllers:MachineController"],
		beego.ControllerComments{
			Method: "GetAll",
			Router: `/`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:MachineController"] = append(beego.GlobalControllerRouter["aserver/controllers:MachineController"],
		beego.ControllerComments{
			Method: "Put",
			Router: `/:id`,
			AllowHTTPMethods: []string{"put"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:MachineController"] = append(beego.GlobalControllerRouter["aserver/controllers:MachineController"],
		beego.ControllerComments{
			Method: "Delete",
			Router: `/:id`,
			AllowHTTPMethods: []string{"delete"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:MailController"] = append(beego.GlobalControllerRouter["aserver/controllers:MailController"],
		beego.ControllerComments{
			Method: "Post",
			Router: `/`,
			AllowHTTPMethods: []string{"post"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:MailController"] = append(beego.GlobalControllerRouter["aserver/controllers:MailController"],
		beego.ControllerComments{
			Method: "GetOne",
			Router: `/:id`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:MailController"] = append(beego.GlobalControllerRouter["aserver/controllers:MailController"],
		beego.ControllerComments{
			Method: "GetAll",
			Router: `/`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:MailController"] = append(beego.GlobalControllerRouter["aserver/controllers:MailController"],
		beego.ControllerComments{
			Method: "Put",
			Router: `/:id`,
			AllowHTTPMethods: []string{"put"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:MailController"] = append(beego.GlobalControllerRouter["aserver/controllers:MailController"],
		beego.ControllerComments{
			Method: "Delete",
			Router: `/:id`,
			AllowHTTPMethods: []string{"delete"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:StorageController"] = append(beego.GlobalControllerRouter["aserver/controllers:StorageController"],
		beego.ControllerComments{
			Method: "Post",
			Router: `/`,
			AllowHTTPMethods: []string{"post"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:StorageController"] = append(beego.GlobalControllerRouter["aserver/controllers:StorageController"],
		beego.ControllerComments{
			Method: "GetOne",
			Router: `/:id`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:StorageController"] = append(beego.GlobalControllerRouter["aserver/controllers:StorageController"],
		beego.ControllerComments{
			Method: "GetAll",
			Router: `/`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:StorageController"] = append(beego.GlobalControllerRouter["aserver/controllers:StorageController"],
		beego.ControllerComments{
			Method: "Put",
			Router: `/:id`,
			AllowHTTPMethods: []string{"put"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:StorageController"] = append(beego.GlobalControllerRouter["aserver/controllers:StorageController"],
		beego.ControllerComments{
			Method: "Delete",
			Router: `/:id`,
			AllowHTTPMethods: []string{"delete"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:ThreshholdController"] = append(beego.GlobalControllerRouter["aserver/controllers:ThreshholdController"],
		beego.ControllerComments{
			Method: "Post",
			Router: `/`,
			AllowHTTPMethods: []string{"post"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:ThreshholdController"] = append(beego.GlobalControllerRouter["aserver/controllers:ThreshholdController"],
		beego.ControllerComments{
			Method: "GetOne",
			Router: `/:id`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:ThreshholdController"] = append(beego.GlobalControllerRouter["aserver/controllers:ThreshholdController"],
		beego.ControllerComments{
			Method: "GetAll",
			Router: `/`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:ThreshholdController"] = append(beego.GlobalControllerRouter["aserver/controllers:ThreshholdController"],
		beego.ControllerComments{
			Method: "Put",
			Router: `/:id`,
			AllowHTTPMethods: []string{"put"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers:ThreshholdController"] = append(beego.GlobalControllerRouter["aserver/controllers:ThreshholdController"],
		beego.ControllerComments{
			Method: "Delete",
			Router: `/:id`,
			AllowHTTPMethods: []string{"delete"},
			Params: nil})

}
