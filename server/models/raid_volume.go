package models

import "time"

type RaidVolume struct {
	Id_RENAME int       `orm:"column(id)"`
	CreatedAt time.Time `orm:"column(created_at);type(datetime)"`
	UpdatedAt time.Time `orm:"column(updated_at);type(datetime)"`
	Raid      string    `orm:"column(raid);size(255);null"`
	Volume    string    `orm:"column(volume);size(255);null"`
	Type      string    `orm:"column(type);size(255)"`
	MachineId string    `orm:"column(machineId);size(255)"`
}
