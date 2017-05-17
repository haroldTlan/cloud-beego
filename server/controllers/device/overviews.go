package device

import (
	"aserver/controllers/web"
	"aserver/models/device"
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
	data, err := device.GetOverViews()
	result := web.NewResponse(data, err)

	c.Data["json"] = &result
	c.ServeJSON()
}
