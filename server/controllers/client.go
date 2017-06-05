package controllers

import (
	"aserver/controllers/web"
	"aserver/models/device"
	"github.com/astaxie/beego"

	"encoding/json"
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
	cs := c.GetString("clients")
	cid := c.GetString("cid")

	var clients []device.ConfClient
	if err := json.Unmarshal([]byte(cs), &clients); err == nil {
		c.Ctx.Output.SetStatus(201)

		err = device.UpdateClient(cid, clients)
		result := web.NewResponse(err, err)
		c.Data["json"] = &result
	} else {
		result := web.NewResponse(err.Error(), err)
		c.Data["json"] = &result
	}

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
