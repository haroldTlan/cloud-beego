package models

import "time"

type NetworkInitiator struct {
	Id_RENAME int       `orm:"column(id)"`
	CreatedAt time.Time `orm:"column(created_at);type(datetime)"`
	UpdatedAt time.Time `orm:"column(updated_at);type(datetime)"`
	Initiator string    `orm:"column(initiator);size(255);null"`
	Eth       string    `orm:"column(eth);size(255);null"`
	Port      int       `orm:"column(port);null"`
	MachineId string    `orm:"column(machineId);size(255)"`
}
