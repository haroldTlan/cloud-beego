package routers

import (
	"github.com/astaxie/beego"
)

func init() {

	beego.GlobalControllerRouter["aserver/controllers/device:DeviceController"] = append(beego.GlobalControllerRouter["aserver/controllers/device:DeviceController"],
		beego.ControllerComments{
			Method: "Post",
			Router: `/`,
			AllowHTTPMethods: []string{"post"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers/device:DeviceController"] = append(beego.GlobalControllerRouter["aserver/controllers/device:DeviceController"],
		beego.ControllerComments{
			Method: "GetDevices",
			Router: `/`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

	beego.GlobalControllerRouter["aserver/controllers/device:StoreViewsController"] = append(beego.GlobalControllerRouter["aserver/controllers/device:StoreViewsController"],
		beego.ControllerComments{
			Method: "GetStoreviews",
			Router: `/`,
			AllowHTTPMethods: []string{"get"},
			Params: nil})

}
