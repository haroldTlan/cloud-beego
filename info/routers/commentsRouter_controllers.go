package routers

import (
	"github.com/astaxie/beego"
)

func init() {

	beego.GlobalControllerRouter["beego_info/controllers:MachineController"] = append(beego.GlobalControllerRouter["beego_info/controllers:MachineController"],
		beego.ControllerComments{
			Method: "Post",
			Router: `/`,
			AllowHTTPMethods: []string{"post"},
			Params: nil})

	beego.GlobalControllerRouter["beego_info/controllers:MachineController"] = append(beego.GlobalControllerRouter["beego_info/controllers:MachineController"],
		beego.ControllerComments{
			Method: "GetOne",
			Router: `/:id`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["beego_info/controllers:MachineController"] = append(beego.GlobalControllerRouter["beego_info/controllers:MachineController"],
		beego.ControllerComments{
			Method: "GetAll",
			Router: `/`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["beego_info/controllers:MachineController"] = append(beego.GlobalControllerRouter["beego_info/controllers:MachineController"],
		beego.ControllerComments{
			Method: "Put",
			Router: `/:id`,
			AllowHTTPMethods: []string{"put"},
			Params: nil})

	beego.GlobalControllerRouter["beego_info/controllers:MachineController"] = append(beego.GlobalControllerRouter["beego_info/controllers:MachineController"],
		beego.ControllerComments{
			Method: "Delete",
			Router: `/:id`,
			AllowHTTPMethods: []string{"delete"},
			Params: nil})

	beego.GlobalControllerRouter["beego_info/controllers:ThreshholdController"] = append(beego.GlobalControllerRouter["beego_info/controllers:ThreshholdController"],
		beego.ControllerComments{
			Method: "Post",
			Router: `/`,
			AllowHTTPMethods: []string{"post"},
			Params: nil})

	beego.GlobalControllerRouter["beego_info/controllers:ThreshholdController"] = append(beego.GlobalControllerRouter["beego_info/controllers:ThreshholdController"],
		beego.ControllerComments{
			Method: "GetOne",
			Router: `/:id`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["beego_info/controllers:ThreshholdController"] = append(beego.GlobalControllerRouter["beego_info/controllers:ThreshholdController"],
		beego.ControllerComments{
			Method: "GetAll",
			Router: `/`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["beego_info/controllers:ThreshholdController"] = append(beego.GlobalControllerRouter["beego_info/controllers:ThreshholdController"],
		beego.ControllerComments{
			Method: "Put",
			Router: `/:id`,
			AllowHTTPMethods: []string{"put"},
			Params: nil})

	beego.GlobalControllerRouter["beego_info/controllers:ThreshholdController"] = append(beego.GlobalControllerRouter["beego_info/controllers:ThreshholdController"],
		beego.ControllerComments{
			Method: "Delete",
			Router: `/:id`,
			AllowHTTPMethods: []string{"delete"},
			Params: nil})

}
