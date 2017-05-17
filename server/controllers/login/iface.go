package login

import (
	"aserver/controllers/web"
	"aserver/models/util"
	"github.com/astaxie/beego"

	"net"
	"strings"
)

// IfaceController operations for ifaces
type IfaceController struct {
	beego.Controller
}

// URLMapping ...
func (c *IfaceController) URLMapping() {
	c.Mapping("GetIfaces", c.GetIfaces)
}

// GetIfaces ...
// @Title Get Ifaces
// @Description get Ifaces
// @Success 200 {object} models.Session
// @Failure 403
// @router / [get]
func (c *IfaceController) GetIfaces() {
	info, err := net.InterfaceAddrs()
	if err != nil {
		util.AddLog(err)
	}

	ifaces := make([]string, 0)
	for _, addr := range info {
		ifaces = append(ifaces, strings.Split(addr.String(), "/")[0])
	}
	result := web.NewResponse(ifaces, err)
	c.Data["json"] = &result
	c.ServeJSON()
}
