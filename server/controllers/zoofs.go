package controllers

import (
	"aserver/controllers/web"
	"aserver/models"
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
}

// Post ...
// @Title Post
// @Description create details
// @Success 201 {int} models.Zoofs
// @Failure 403 body is empty
// @router / [post]
func (c *ZoofsController) Post() {
	export := c.GetString("export")
	expand := c.GetString("expand")
	client := c.GetString("client")
	id := c.GetString("id")
	err := models.Zoofs(export, expand, client, id)
	result := web.NewResponse(err, err)
	c.Data["json"] = &result
	c.ServeJSON()
}
