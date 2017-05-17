package ansible

import (
	"aserver/controllers/web"
	"github.com/astaxie/beego"

	"aserver/models/ansible"
	"fmt"
	_ "strings"
)

type Session struct {
	Id int32 `json:"login_id"`
}

// AnsibleController operations for Login
type AnsibleController struct {
	beego.Controller
}

// URLMapping ...
func (c *AnsibleController) URLMapping() {
	c.Mapping("Post", c.Post)
}

// Post ...
// @Title Post
// @Description Ansible
// @Param   body        body    models.Ansible  true        "body for Session content"
// @Success 201 {int} models.Ansible
// @Failure 403 body is empty
// @router / [post]
func (c *AnsibleController) Post() {
	var err error
	act, err := c.GetBool("active")
	//ansible gateway -m command -a "service packetbeat start"

	ansible.Active(act)
	fmt.Println(act)
	result := web.NewResponse(err, err)
	c.Data["json"] = &result
	c.ServeJSON()
}
