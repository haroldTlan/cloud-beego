package controllers

import (
	"aserver/controllers/web"
	"aserver/models/device"
	"github.com/astaxie/beego"
	_ "time"
)

// ClientController operations for Setting
type ClientController struct {
	beego.Controller
}

// URLMapping ...
func (c *ClientController) URLMapping() {
	c.Mapping("Post", c.Post)
	c.Mapping("Delete", c.Delete)
}

// Post ...
// @Title Post
// @Description create details
// @Success 201 {int} models.Client
// @Failure 403 body is empty
// @router / [post]
func (c *ClientController) Post() {
	ip := c.GetString("ip")
	cid := c.GetString("cid")

	err := device.AddClient(ip, cid)
	result := web.NewResponse(err, err)
	c.Data["json"] = &result
	c.ServeJSON()
}

// Delete ...
// @Title Delete
// @Description remove the Client
// @Param   id      path    string  true        "The id you want to delete"
// @Success 200 {string} delete success!
// @Failure 403 id is empty
// @router /:uuid [delete]
func (c *ClientController) Delete() {
	idStr := c.Ctx.Input.Param(":uuid")
	err := device.DelClient(idStr)
	result := web.NewResponse(err, err)
	c.Data["json"] = result
	c.ServeJSON()
}
