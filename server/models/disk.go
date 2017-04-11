package models

type Disk struct {
	Uuid      string `orm:"column(uuid);size(64);null"`
	Location  string `orm:"column(location);size(64);null"`
	MachineId string `orm:"column(machineId);size(64);null"`
	Health    string `orm:"column(health);size(64);null"`
	Role      string `orm:"column(role);size(64);null"`
	CapSector int64  `orm:"column(cap_sector)"`
	Raid      string `orm:"column(raid);size(64);null"`
	Vendor    string `orm:"column(vendor);size(64);null"`
	Model     string `orm:"column(model);size(64);null"`
	Sn        string `orm:"column(sn);size(64);null"`
}
