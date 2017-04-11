package models

type Raid struct {
	Uuid      string `orm:"column(uuid);size(64);null"`
	Health    string `orm:"column(health);size(64);null"`
	MachineId string `orm:"column(machineId);size(64);null"`
	Level     string `orm:"column(level);size(64);null"`
	Name      string `orm:"column(name);size(64);null"`
	Cap       int    `orm:"column(cap);null"`
	UsedCap   int    `orm:"column(used_cap);null"`
	Deleted   int8   `orm:"column(deleted);null"`
}
