package controllers

import (
	"aserver/controllers/web"
	"aserver/models/device"
	"encoding/json"
	"github.com/astaxie/beego"
	_ "time"
)

// StorageController operations for Setting
type StorageController struct {
	beego.Controller
}

// URLMapping ...
func (c *StorageController) URLMapping() {
	c.Mapping("Post", c.Post)
	c.Mapping("Delete", c.Delete)
}

// Post ...
// @Title Post
// @Description create details
// @Success 201 {int} models.Storage
// @Failure 403 body is empty
// @router / [post]
func (c *StorageController) Post() {
	var v []device.Rest
	test := c.GetString("rest")

	if err := json.Unmarshal([]byte(test), &v); err == nil {
		c.Ctx.Output.SetStatus(201)
		err = device.RestInit(v)
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
// @Description remove the Storage
// @Param   id      path    string  true        "The id you want to delete"
// @Success 200 {string} delete success!
// @Failure 403 id is empty
// @router /:uuid [delete]
func (c *StorageController) Delete() {
	idStr := c.Ctx.Input.Param(":uuid")
	err := device.RestRemove(idStr)
	result := web.NewResponse(err, err)
	c.Data["json"] = &result
	c.ServeJSON()
}
