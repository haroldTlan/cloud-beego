package device

import (
	"aserver/models"
	"aserver/models/device"
	_ "fmt"
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
}

// Post ...
// @Title Post
// @Description create Devices
// @Param   body        body    models.device  true        "body for Device content"
// @Success 201 {int} models.Device
// @Failure 403 body is empty
// @router / [post]
func (c *DeviceController) Post() {
	ip := c.GetString("ip")
	version := c.GetString("version")
	devtype := c.GetString("devtype")
	size := c.GetString("size")
	cluster := c.GetString("cluster")

	if err := device.InsertDevice(ip, version, size, devtype, cluster); err == nil {
		c.Ctx.Output.SetStatus(201)
		c.Data["json"] = 22
	} else {
		c.Data["json"] = err.Error()
	}
	c.ServeJSON()
}

// GetDevices ...
// @Title Get Devices
// @Description get devices
// @Success 200 {object} models.Device
// @Failure 403
// @router / [get]
func (c *DeviceController) GetDevices() {
	//get all devices
	data, err := device.SelectAllDevices()
	if err != nil {
		c.Data["json"] = models.NewResponse("error", err)
	}
	c.Data["json"] = models.NewResponse("success", data)
	c.ServeJSON()
}
