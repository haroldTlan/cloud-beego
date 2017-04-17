package login

import (
	"aserver/controllers/web"
	"github.com/astaxie/beego"
)

// SystemInfoController operations for Login
type SystemInfoController struct {
	beego.Controller
}

// URLMapping ...
func (c *SystemInfoController) URLMapping() {
	c.Mapping("Get", c.Get)
}

// GetSystemInfo ...
// @Title Get SystemInfo
// @Description get systeminfo
// @Success 200 {object} models.SystemInfo
// @Failure 403
// @router / [get]
func (c *SystemInfoController) Get() {
	feature := make([]string, 0)
	feature = append(feature, "xfs")

	systeminfo := make(map[string]interface{})
	systeminfo["gui version"] = "2.7.3"
	systeminfo["version"] = "2.2"
	systeminfo["feature"] = feature

	result := web.NewResponse(systeminfo, nil)
	c.Data["json"] = &result
	c.ServeJSON()
}
