package models

import "time"

type Initiator struct {
	Wwn       string    `orm:"column(wwn);size(64);null"`
	CreatedAt time.Time `orm:"column(created_at);type(datetime);null"`
	UpdatedAt time.Time `orm:"column(updated_at);type(datetime);null"`
	TargetWwn string    `orm:"column(target_wwn);size(64);null"`
	MachineId string    `orm:"column(machineId);size(64);null"`
}
