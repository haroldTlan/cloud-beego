package controllers

import (
	"aserver/controllers/web"
	"aserver/models/device"
	"github.com/astaxie/beego"
	_ "time"
)

// ZoofsController operations for Setting
type ZoofsController struct {
	beego.Controller
}

// URLMapping ...
func (c *ZoofsController) URLMapping() {
	c.Mapping("Post", c.Post)
	c.Mapping("Delete", c.Delete)
}

// Post ...
// @Title Post
// @Description create details
// @Success 201 {int} models.Zoofs
// @Failure 403 body is empty
// @router / [post]
func (c *ZoofsController) Post() {
	cid := c.GetString("uuid") //uuid
	level, err := c.GetInt("level")
	if err != nil {
		result := web.NewResponse(err.Error(), err)
		c.Data["json"] = &result
		c.ServeJSON()
		return
	}
	err = device.Zoofs(cid, level) //(export, expand, client, id, level)
	result := web.NewResponse(err, err)
	c.Data["json"] = &result
	c.ServeJSON()
}

// Delete ...
// @Title Delete
// @Description delete the zoofs
// @Param   id      path    string  true        "The id you want to delete"
// @Success 200 {string} delete success!
// @Failure 403 id is empty
// @router /:uuid [delete]
func (c *ZoofsController) Delete() {
	idStr := c.Ctx.Input.Param(":uuid")
	err := device.DelZoofs(idStr)
	result := web.NewResponse(err, err)
	c.Data["json"] = result
	c.ServeJSON()
}
