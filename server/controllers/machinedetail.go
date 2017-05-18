package controllers

import (
	"aserver/controllers/web"
	"aserver/models"
	"github.com/astaxie/beego"
)

// MachineDetailsController operations for Journals
type MachineDetailsController struct {
	beego.Controller
}

// URLMapping ...
func (c *MachineDetailsController) URLMapping() {
	c.Mapping("Post", c.Post)
	c.Mapping("Get", c.Get)
}

// GetAll ...
// @Title Get All
// @Description get restapi
// @Success 200 {object} models.Details
// @Failure 403
// @router / [get]
func (c *MachineDetailsController) Get() {
	rest, err := models.RestApi()
	result := web.NewResponse(rest, err)

	c.Data["json"] = &result
	c.ServeJSON()
}
