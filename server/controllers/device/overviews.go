package device

import (
	"fmt"
	"github.com/astaxie/beego"
)

// StoreViewsController operations for Storeviews
type StoreViewsController struct {
	beego.Controller
}

// URLMapping ...
func (c *StoreViewsController) URLMapping() {
	//      c.Mapping("Post", c.Post)
	c.Mapping("GetStoreviews", c.GetStoreviews)
}

// GetStoreviews ...
// @Title Get Storeviews
// @Description get storeviews
// @Success 200 {object} models.Device
// @Failure 403
// @router / [get]
func (c *StoreViewsController) GetStoreviews() {
	fmt.Println("aaaaaaaaa")
	c.Data["json"] = 111
	c.ServeJSON()
}
