package controllers

import (
	"aserver/controllers/web"
	"aserver/models"
	"github.com/astaxie/beego"
	"strconv"
)

// JournalsController operations for Journals
type JournalsController struct {
	beego.Controller
}

// URLMapping ...
func (c *JournalsController) URLMapping() {
	c.Mapping("Post", c.Post)
	c.Mapping("Get", c.Get)
}

// Post ...
// @Title Post
// @Description create Journals
// @Param	body		body 	models.Journals	true		"body for Journals content"
// @Success 201 {int} models.Journals
// @Failure 403 body is empty
// @router / [post]
func (c *JournalsController) Post() {
	aColumns := []string{
		"CreatedAt",
		"Level",
		"Status",
		"ChineseMessage",
	}

	output, count, counts := models.Datatables(aColumns, c.Ctx.Input)
	data := make(map[string]interface{}, count)
	data["sEcho"], _ = strconv.Atoi(c.Ctx.Input.Query("sEcho"))
	data["iTotalRecords"] = counts
	data["iTotalDisplayRecords"] = count
	data["aaData"] = output
	c.Data["json"] = data
	c.ServeJSON()
}

// Get ...
// @Title Get Journals(emergency +TODO)
// @Description get journals
// @Success 200 {object} models.Journals
// @Failure 403
// @router / [get]
func (c *JournalsController) Get() {
	journals, err := models.GetJournals()
	result := web.NewResponse(journals, err)
	c.Data["json"] = &result
	c.ServeJSON()
}
