package models

import (
	"github.com/astaxie/beego/orm"
	"strings"
	_ "time"
)

type Export struct {
	ExportInit `orm:"auto"`
	//Role    string `orm:"column(role);size(64);null"`
	//Virtual string `orm:"column(virtual);size(64);null"`
}

func (t *Export) TableName() string {
	return "export"
}

func init() {
	orm.RegisterModel(new(Export))
}

func Zoofs(ip, expand, client, id string) (err error) {
	o := orm.NewOrm()

	var e Export
	num, err := o.QueryTable(new(Export)).Filter("ip", ip).All(&e)
	if err != nil {
		AddLog(err)
	}
	e.Clusterid = id
	e.Status = true

	if num == 0 {
		if _, err := o.Insert(&e); err != nil {
			AddLog(err)
		}
	} else {
		if _, err := o.Update(&e); err != nil {
			AddLog(err)
		}
	}

	for _, ex := range strings.Split(expand, ",") {
		var s Storage
		num, err := o.QueryTable(new(Storage)).Filter("ip", ex).All(&s)
		if err != nil {
			AddLog(err)
		}
		s.Clusterid = id
		s.Status = true
		if num == 0 {
			if _, err := o.Insert(&s); err != nil {
				AddLog(err)
			}
		} else {
			if _, err := o.Update(&s); err != nil {
				AddLog(err)
			}
		}
	}

	var c Client
	num, err = o.QueryTable(new(Client)).Filter("ip", ip).All(&c)
	if err != nil {
		AddLog(err)
	}
	c.Clusterid = id
	c.Status = true

	if num == 0 {
		if _, err := o.Insert(&c); err != nil {
			AddLog(err)
		}
	} else {
		if _, err := o.Update(&c); err != nil {
			AddLog(err)
		}
	}
	return
}
