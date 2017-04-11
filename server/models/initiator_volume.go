package models

import "time"

type InitiatorVolume struct {
	Id_RENAME int       `orm:"column(id)"`
	CreatedAt time.Time `orm:"column(created_at);type(datetime)"`
	UpdatedAt time.Time `orm:"column(updated_at);type(datetime)"`
	Initiator string    `orm:"column(initiator);size(255);null"`
	Volume    string    `orm:"column(volume);size(255);null"`
	MachineId string    `orm:"column(machineId);size(255)"`
}
