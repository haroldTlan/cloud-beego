package controllers

import (
	"aserver/controllers/web"
	"aserver/models/device"

	"github.com/astaxie/beego"
)

// ClustersController operations for Journals
type ClustersController struct {
	beego.Controller
}

// URLMapping ...
func (c *ClustersController) URLMapping() {
	c.Mapping("Post", c.Post)
	c.Mapping("Get", c.Get)
}

// GetAll ...
// @Title Get Clusters
// @Description get clusters
// @Success 200 {object} models.Clusters
// @Failure 403
// @router / [get]
func (c *ClustersController) Get() {
	clus, err := device.GetClusters()
	result := web.NewResponse(clus, err)

	c.Data["json"] = &result
	c.ServeJSON()

}

// Post ...
// @Title Post
// @Description create clusters
// @Success 201 {int} models.Clusters
// @Failure 403 body is empty
// @router / [post]
func (c *ClustersController) Post() {
	clu, err := c.GetInt("cluster")

	if err != nil {
		result := web.NewResponse(err.Error(), err)
		c.Data["json"] = &result
		c.ServeJSON()
		return
	}

	e := c.GetString("export") //All is ip
	s := c.GetString("storage")
	client := c.GetString("client")
	err = device.AddClusters(clu, e, s, client)
	result := web.NewResponse(err, err)

	c.Data["json"] = &result
	c.ServeJSON()
}

// Delete ...
// @Title Delete
// @Description delete the cluster
// @Param   id      path    string  true        "The id you want to delete"
// @Success 200 {string} delete success!
// @Failure 403 id is empty
// @router /:uuid [delete]
func (c *ClustersController) Delete() {
	idStr := c.Ctx.Input.Param(":uuid")
	err := device.DelClusters(idStr)
	result := web.NewResponse(err, err)
	c.Data["json"] = result
	c.ServeJSON()
}
