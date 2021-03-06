package device

import (
	"aserver/controllers/web"
	"aserver/models/device"

	"github.com/astaxie/beego"
)

// DeviceController operations for Devices
type DeviceController struct {
	beego.Controller
}

// URLMapping ...
func (c *DeviceController) URLMapping() {
	c.Mapping("Post", c.Post)
	c.Mapping("GetDevices", c.GetDevices)
	c.Mapping("Del", c.Del)
}

// Post ...
// @Title Post
// @Description create Devices
// @Param   body        body    models.device  true        "body for Device content"
// @Success 201 {int} models.Device
// @Failure 403 body is empty
// @router / [post]
func (c *DeviceController) Post() {
	var result map[string]interface{}
	ip := c.GetString("ip")
	version := c.GetString("version")
	devtype := c.GetString("devtype")
	size := c.GetString("size")

	err := device.AddDevice(ip, version, size, devtype)
	result = web.NewResponse(err, err)
	//c.Ctx.Output.SetStatus(201)

	c.Data["json"] = &result
	c.ServeJSON()
}

// GetDevices ...
// @Title Get Devices
// @Description get devices
// @Success 200 {object} models.Device
// @Failure 403
// @router / [get]
func (c *DeviceController) GetDevices() {
	data, err := device.GetAllDevices()
	result := web.NewResponse(data, err)

	c.Data["json"] = &result
	c.ServeJSON()
}

// Delete ...
// @Title Delete
// @Description delete the Device
// @Param   id      path    string  true        "The id you want to delete"
// @Success 200 {string} delete success!
// @Failure 403 id is empty
// @router /:uuid [delete]
func (c *DeviceController) Del() {
	idStr := c.Ctx.Input.Param(":uuid")
	err := device.DeleteDevice(idStr)
	result := web.NewResponse(err, err)

	c.Data["json"] = &result
	c.ServeJSON()
}
