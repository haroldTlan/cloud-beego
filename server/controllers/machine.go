package controllers

import (
	"aserver/controllers/web"
	"aserver/models"
	"encoding/json"
	"errors"
	"strconv"
	"strings"

	"github.com/astaxie/beego"
)

// MachineController operations for Machine
type MachineController struct {
	beego.Controller
}

// URLMapping ...
func (c *MachineController) URLMapping() {
	c.Mapping("Post", c.Post)
	c.Mapping("GetAll", c.GetAll)
	c.Mapping("Put", c.Put)
	c.Mapping("Delete", c.Delete)
}

// Post ...
// @Title Post
// @Description create Machine
// @Param	body		body 	models.Machine	true		"body for Machine content"
// @Success 201 {int} models.Machine
// @Failure 403 body is empty
// @router / [post]
func (c *MachineController) Post() {
	var result map[string]interface{}
	ip := c.GetString("ip")
	slotnr, err := c.GetInt("slotnr")
	if err != nil {
		models.AddLog(err)
	}

	devtype := c.GetString("devtype")
	role := c.GetString("role")
	cluster := c.GetString("cluster")

	if err := models.AddMachine(ip, devtype, role, cluster, slotnr); err == nil {
		c.Ctx.Output.SetStatus(201)
		result = web.NewResponse(err, err)
	} else {
		models.AddLog(err)
		result = web.NewResponse(err, err)
	}
	c.Data["json"] = result
	c.ServeJSON()
}

// GetAll ...
// @Title Get All
// @Description get Machine
// @Param	query	query	string	false	"Filter. e.g. col1:v1,col2:v2 ..."
// @Param	fields	query	string	false	"Fields returned. e.g. col1,col2 ..."
// @Param	sortby	query	string	false	"Sorted-by fields. e.g. col1,col2 ..."
// @Param	order	query	string	false	"Order corresponding to each sortby field, if single value, apply to all sortby fields. e.g. desc,asc ..."
// @Param	limit	query	string	false	"Limit the size of result set. Must be an integer"
// @Param	offset	query	string	false	"Start position of result set. Must be an integer"
// @Success 200 {object} models.Machine
// @Failure 403
// @router / [get]
func (c *MachineController) GetAll() {
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
				errs := errors.New("Error: invalid query key/value pair")
				c.Data["json"] = errs
				models.AddLog(errs)
				c.ServeJSON()
				return
			}
			k, v := kv[0], kv[1]
			query[k] = v
		}
	}

	l, err := models.GetAllMachine(query, fields, sortby, order, offset, limit)
	result := web.NewResponse(l, err)
	c.Data["json"] = &result
	c.ServeJSON()
}

// Put ...
// @Title Put
// @Description update the Machine
// @Param	id		path 	string	true		"The id you want to update"
// @Param	body		body 	models.Machine	true		"body for Machine content"
// @Success 200 {object} models.Machine
// @Failure 403 :id is not int
// @router /:id [put]
func (c *MachineController) Put() {
	var result map[string]interface{}
	idStr := c.Ctx.Input.Param(":id")
	id, _ := strconv.Atoi(idStr)
	v := models.Machine{Id: id}
	if err := json.Unmarshal(c.Ctx.Input.RequestBody, &v); err == nil {
		if err := models.UpdateMachineById(&v); err == nil {
			result = web.NewResponse("Ok", err)
		} else {
			result = web.NewResponse(err, err)
			models.AddLog(err)
		}
	} else {
		result = web.NewResponse(err, err)
		models.AddLog(err)
	}
	c.Data["json"] = result
	c.ServeJSON()
}

// Delete ...
// @Title Delete
// @Description delete the Machine
// @Param	id		path 	string	true		"The id you want to delete"
// @Success 200 {string} delete success!
// @Failure 403 id is empty
// @router /:uuid [delete]
func (c *MachineController) Delete() {
	idStr := c.Ctx.Input.Param(":uuid")
	err := models.DeleteMachine(idStr)
	result := web.NewResponse(err, err)
	c.Data["json"] = result
	c.ServeJSON()
}
