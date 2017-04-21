package controllers

import (
	"aserver/controllers/web"
	"aserver/models"
	"errors"
	"strconv"
	"strings"

	"github.com/astaxie/beego"
)

// MailController operations for Mail
type MailController struct {
	beego.Controller
}

// URLMapping ...
func (c *MailController) URLMapping() {
	c.Mapping("Post", c.Post)
	c.Mapping("Put", c.Put)
	c.Mapping("Delete", c.Delete)
}

// Post ...
// @Title Post
// @Description create Mail
// @Param	body		body 	models.Mail	true		"body for Mail content"
// @Success 201 {int} models.Mail
// @Failure 403 body is empty
// @router / [post]
func (c *MailController) Post() {
	address := c.GetString("address")
	level := c.GetString("level")
	ttl := c.GetString("ttl")

	err := models.AddMail(address, level, ttl)
	result := web.NewResponse(err, err)
	c.Data["json"] = &result
	c.ServeJSON()
}

// GetAll ...
// @Title Get All
// @Description get Mail
// @Param	query	query	string	false	"Filter. e.g. col1:v1,col2:v2 ..."
// @Param	fields	query	string	false	"Fields returned. e.g. col1,col2 ..."
// @Param	sortby	query	string	false	"Sorted-by fields. e.g. col1,col2 ..."
// @Param	order	query	string	false	"Order corresponding to each sortby field, if single value, apply to all sortby fields. e.g. desc,asc ..."
// @Param	limit	query	string	false	"Limit the size of result set. Must be an integer"
// @Param	offset	query	string	false	"Start position of result set. Must be an integer"
// @Success 200 {object} models.Mail
// @Failure 403
// @router / [get]
func (c *MailController) GetAll() {
	var fields []string
	var sortby []string
	var order []string
	var query = make(map[string]string)
	var limit int64 = 10
	var offset int64

	// fields: col1,col2,entity.col3
	if v := c.GetString("fields"); v != "" {
		fields = strings.Split(v, ",")
	}
	// limit: 10 (default is 10)
	if v, err := c.GetInt64("limit"); err == nil {
		limit = v
	}
	// offset: 0 (default is 0)
	if v, err := c.GetInt64("offset"); err == nil {
		offset = v
	}
	// sortby: col1,col2
	if v := c.GetString("sortby"); v != "" {
		sortby = strings.Split(v, ",")
	}
	// order: desc,asc
	if v := c.GetString("order"); v != "" {
		order = strings.Split(v, ",")
	}
	// query: k:v,k:v
	if v := c.GetString("query"); v != "" {
		for _, cond := range strings.Split(v, ",") {
			kv := strings.SplitN(cond, ":", 2)
			if len(kv) != 2 {
				c.Data["json"] = errors.New("Error: invalid query key/value pair")
				c.ServeJSON()
				return
			}
			k, v := kv[0], kv[1]
			query[k] = v
		}
	}

	l, err := models.GetAllMail(query, fields, sortby, order, offset, limit)
	result := web.NewResponse(l, err)
	c.Data["json"] = &result

	c.ServeJSON()
}

// Put ...
// @Title Put
// @Description update the Mail
// @Param	id		path 	string	true		"The id you want to update"
// @Param	body		body 	models.Mail	true		"body for Mail content"
// @Success 200 {object} models.Mail
// @Failure 403 :id is not int
// @router /:id [put]
func (c *MailController) Put() {
	idStr := c.Ctx.Input.Param(":id")
	id, _ := strconv.Atoi(idStr)
	level, err := c.GetInt("level")
	if err != nil {
		result := web.NewResponse(err, err)
		c.Data["json"] = &result
		c.ServeJSON()
		return
	}
	ttl, err := c.GetInt("ttl")
	if err != nil {
		result := web.NewResponse(err, err)
		c.Data["json"] = &result
		c.ServeJSON()
		return
	}

	err = models.UpdateMailById(id, level, ttl)
	result := web.NewResponse(err, err)
	c.Data["json"] = &result
	c.ServeJSON()
}

// Delete ...
// @Title Delete
// @Description delete the Machine
// @Param   id      path    string  true        "The id you want to delete"
// @Success 200 {string} delete success!
// @Failure 403 id is empty
// @router /:id [delete]
func (c *MailController) Delete() {
	idStr := c.Ctx.Input.Param(":id")

	err := models.DeleteMail(idStr)
	result := web.NewResponse(err, err)
	c.Data["json"] = result
	c.ServeJSON()
}
