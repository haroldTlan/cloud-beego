package login

import (
	"github.com/astaxie/beego"
)

type Session struct {
	Id int32 `json:"login_id"`
}

// LoginController operations for Login
type LoginController struct {
	beego.Controller
}

// URLMapping ...
func (c *LoginController) URLMapping() {
	c.Mapping("Post", c.Post)
}

// Post ...
// @Title Post
// @Description Get Session
// @Param   body        body    models.Session  true        "body for Session content"
// @Success 201 {int} models.Session
// @Failure 403 body is empty
// @router / [post]
func (c *LoginController) Post() {
	sess := Session{Id: 111}

	c.Data["json"] = &sess
	c.ServeJSON()
}
