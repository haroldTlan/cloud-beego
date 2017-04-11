package models

type Volume struct {
	Uuid      string `orm:"column(uuid);size(64);null"`
	Health    string `orm:"column(health);size(64);null"`
	MachineId string `orm:"column(machineId);size(64);null"`
	Name      string `orm:"column(name);size(64);null"`
	Used      int    `orm:"column(used);null"`
	OwnerType string `orm:"column(owner_type);size(64);null"`
	Cap       int64  `orm:"column(cap)"`
	Deleted   int8   `orm:"column(deleted);null"`
}
