package models

import (
	"time"
)

type Disks struct {
	Uuid      string  `orm:"column(uuid);size(64);pk" json:"id"`
	Health    string  `orm:"column(health);size(64)" json:"health"`
	Role      string  `orm:"column(role);size(64)" json:"role"`
	Location  string  `orm:"column(location);size(64)" json:"location"`
	Raid      string  `orm:"column(raid);size(64)"  json:"raid"`
	CapSector int64   `orm:"column(cap_sector)" json:"cap_sector"`
	CapMb     float64 `orm:"column(cap_mb)" json:"cap_mb"`
	Vendor    string  `orm:"column(vendor);size(64)" json:"vendor"`
	Model     string  `orm:"column(model);size(64)" json:"model"`
	Sn        string  `orm:"column(sn);size(64)" json:"sn"`
	Machineid string  `orm:"column(machineid);size(64)" json:"machineid"`
}

type Raids struct {
	Uuid      string  `orm:"column(uuid);size(64);pk" json:"id"`
	Health    string  `orm:"column(health);size(64)" json:"health"`
	Level     int64   `orm:"column(level)" json:"level"`
	Name      string  `orm:"column(name);size(64)" json:"name"`
	Cap       int64   `orm:"column(cap)" json:"cap_sector"`
	Used      int64   `orm:"column(used)" json:"used_cap_sector"`
	CapMb     float64 `orm:"column(cap_mb)" json:"cap_mb"`
	UsedMb    float64 `orm:"column(used_mb)" json:"used_cap_mb"`
	Machineid string  `orm:"column(machineid);size(64)" json:"machineid"`
}
type Volumes struct {
	Uuid      string  `orm:"column(uuid);size(64);pk" json:"id"`
	Health    string  `orm:"column(health);size(64)" json:"health"`
	Name      string  `orm:"column(name);size(64)" json:"name"`
	Cap       int64   `orm:"column(cap)" json:"cap_sector"`
	CapMb     float64 `orm:"column(cap_mb)" json:"cap_mb"`
	Owner     string  `orm:"column(owner);size(64)" json:"owner"`
	Used      bool    `orm:"column(used)" json:"used"`
	Machineid string  `orm:"column(machineid);size(64)" json:"machineid"`
}

type Inits struct {
	Portals   []string `json:"portals"`
	Wwn       string   `json:"wwn"`
	Id        string   `json:"id"`
	Volumes   []string `json:"volumes"`
	Active    bool     `json:"active_session"`
	Machineid string   `orm:"column(machineid);size(64)"`
}

type Initiators struct {
	Portals   string `orm:"column(portals);size(64);pk"`
	Wwn       string `orm:"column(wwn);size(64)"`
	Id        string `orm:"column(id);size(64)" json:"id"`
	Volumes   string `orm:"column(volumes);size(10)"`
	Active    bool   `orm:"column(active)"`
	Machineid string `orm:"column(machineid);size(64)"`
}

type Fs struct {
	Uuid      string `orm:"column(uuid);size(64);pk" json:"id""`
	Volume    string `orm:"column(volume);size(64)" json:"volume"`
	Name      string `orm:"column(name);size(64)" json:"name"`
	Type      string `orm:"column(type);size(64)" json:"type"`
	Machineid string `orm:"column(machineid);size(64)" json:"machineid"`
}
type Journals struct {
	Message   string    `orm:"column(message);size(64);pk" json:"message"`
	Created   time.Time `orm:"column(created);type(datetime)"  json:"created"`
	Unix      int64     `orm:"column(created_at)" json:"created_at"`
	Level     string    `orm:"column(level);size(64)" json:"level"`
	Machineid string    `orm:"column(machineid);size(64)" json:"machineid"`
}
