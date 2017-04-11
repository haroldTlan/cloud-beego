package routers

import (
	"github.com/astaxie/beego"
)

func init() {

	beego.GlobalControllerRouter["aserver/controllers/login:LoginController"] = append(beego.GlobalControllerRouter["aserver/controllers/login:LoginController"],
		beego.ControllerComments{
			Method: "Post",
			Router: `/`,
			AllowHTTPMethods: []string{"post"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers/login:LoginController"] = append(beego.GlobalControllerRouter["aserver/controllers/login:LoginController"],
		beego.ControllerComments{
			Method: "GetIfaces",
			Router: `/`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

}
