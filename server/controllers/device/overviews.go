package device

import (
	"aserver/controllers/web"
	"aserver/models/device"
	"aserver/models/util"
	"github.com/astaxie/beego"
)

// StoreViewsController operations for Storeviews
type StoreViewsController struct {
	beego.Controller
}

// URLMapping ...
func (c *StoreViewsController) URLMapping() {
	c.Mapping("GetStoreviews", c.GetStoreviews)
}

// GetStoreviews ...
// @Title Get Storeviews
// @Description get storeviews
// @Success 200 {object} models.Device
// @Failure 403
// @router / [get]
func (c *StoreViewsController) GetStoreviews() {
	var result map[string]interface{}
	data, err := device.GetOverViews()
	if err == nil {
		result = web.NewResponse(data, err)
	} else {
		util.AddLog(err)
		result = web.NewResponse("error", err)
	}
	c.Data["json"] = &result
	c.ServeJSON()
}
