package models

import (
	_ "time"

	"github.com/astaxie/beego/orm"
)

type Storage struct {
	ExportInit
	Master string `json:"master"`
	Cid    int    `json:"cid"`
	Sid    int    `json:"sid"`
	Slot   string `json:"slot"`
}

func (t *Storage) TableName() string {
	return "storage"
}

func init() {
	orm.RegisterModel(new(Storage))
}
