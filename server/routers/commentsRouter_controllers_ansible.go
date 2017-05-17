package routers

import (
	"github.com/astaxie/beego"
)

func init() {

	beego.GlobalControllerRouter["aserver/controllers/ansible:AnsibleController"] = append(beego.GlobalControllerRouter["aserver/controllers/ansible:AnsibleController"],
		beego.ControllerComments{
			Method: "Post",
			Router: `/`,
			AllowHTTPMethods: []string{"post"},
			Params: nil})

}
