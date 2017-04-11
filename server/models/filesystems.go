package models

import "time"

type Filesystems struct {
	Uuid       string    `orm:"column(uuid);size(64);null"`
	CreatedAt  time.Time `orm:"column(created_at);type(datetime);null"`
	UpdatedAt  time.Time `orm:"column(updated_at);type(datetime);null"`
	MachineId  string    `orm:"column(machineId);size(64);null"`
	Volume     string    `orm:"column(volume);size(64);null"`
	Name       string    `orm:"column(name);size(64);null"`
	ChunkKb    int       `orm:"column(chunk_kb);null"`
	Mountpoint string    `orm:"column(mountpoint);size(64);null"`
	Type       string    `orm:"column(type);size(64);null"`
}
