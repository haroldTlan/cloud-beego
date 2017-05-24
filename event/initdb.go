package main

import (
	"time"
)

type Cluster struct {
	Cid     int       `orm:"column(cid);pk"`
	Uuid    string    `orm:"column(uuid);size(255)"`
	Zoofs   bool      `orm:"column(zoofs)"`
	Store   bool      `orm:"column(store)"`
	Created time.Time `orm:"column(created);type(datetime)"`
}

type Storage struct {
	Id        int       `orm:"column(uid);auto" json:"uid"`
	Uuid      string    `orm:"column(uuid);size(64);null" json:"uuid"`
	Ip        string    `orm:"column(ip);size(64);null" json:"ip"`
	Version   string    `orm:"column(version);size(64);null" json:"version"`
	Size      string    `orm:"column(size);size(64);null" json:"size"`
	Clusterid string    `orm:"column(clusterid);size(64);null" json:"clusterid"`
	Status    bool      `orm:"column(status);null" json:"status"`
	Created   time.Time `orm:"column(created);type(datetime);null" json:"created"`
	Devtype   string    `orm:"column(devtype);size(64);null" json:"devtype"`
	Master    string    `json:"master"`
	Cid       int       `json:"cid"`
	Sid       int       `json:"sid"`
	Slot      string    `json:"slot"`
}

type Cmd struct {
	Event     string `json:"event"`
	Ip        string `json:"ip"`
	Status    bool   `json:"status"`
	Detail    string `json:"detail"`
	MachineId string `json:"machineId"`
}

type HeartBeat struct {
	Event     string `json:"event"`
	Ip        string `json:"ip"`
	MachineId string `json:"machineId"`
}

type DiskUnplugged struct {
	Event     string `json:"event"`
	Uuid      string `json:"uuid"`
	Location  string `json:"location"`
	DevName   string `json:"dev_name"`
	Ip        string `json:"ip"`
	MachineId string `json:"machineId"`
}

type DiskPlugged struct {
	Event     string `json:"event"`
	Uuid      string `json:"uuid"`
	Ip        string `json:"ip"`
	MachineId string `json:"machineId"`
}

type RaidRemove struct {
	Event     string   `json:"event"`
	Uuid      string   `json:"uuid"`
	RaidDisks []string `json:"raid_disks"`
	Ip        string   `json:"ip"`
	MachineId string   `json:"machineId"`
}

type FsSystem struct {
	Event     string `json:"event"`
	Type      string `json:"type"`
	Volume    string `json:"volume"`
	Ip        string `json:"ip"`
	MachineId string `json:"machineId"`
}

type Warning struct {
	Event  string  `json:"event"`
	Type   string  `json:"type"`
	Ip     string  `json:"ip"`
	Value  float64 `json:"value"`
	Status string  `json:"status"`
}

type Safety struct {
	Event string `json:"event"`
	Ip    string `json:"ip"`
}

type Machine struct {
	Uid     int       `orm:"pk" json:"uid"`
	Uuid    string    `json:"uuid"`
	Ip      string    `json:"ip"`
	Devtype string    `json:"ip"`
	Slotnr  int       `json:"slotnr"`
	Created time.Time `orm:"index" json:"created"`
	Status  bool      `json:"status"`
}

type Journal struct {
	Journals
	MachineId string `orm:"column(machineId)" json:"machineId"`
}

type Emergency struct {
	Uid            int       `orm:"pk" json:"uid"`
	Created_at     time.Time `orm:"index" json:"created"`
	Updated_at     time.Time `orm:"index" json:"updated"`
	Ip             string    `json:"ip"`
	Event          string    `json:"event"`
	Level          string    `json:"level"`
	Message        string    `json:"message"`
	ChineseMessage string    `json:"chinese_message"`
	Status         bool      `json:"status"`
}

type Mail struct {
	Uid     int    `orm:"pk" json:"uid"`
	Address string `json:"address"`
	Level   int    `json:"level"`
	Ttl     int    `json:"ttl"`
}

type Log struct {
	Message    string `json:"message"`
	Created_at int64  `json:"created_at"`
	Level      string `json:"level"`
	Source     string `json:"scource"`
}

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
type ExportInit struct {
	Id        int       `orm:"column(uid);auto" json:"uid"`
	Uuid      string    `orm:"column(uuid);size(64);null" json:"uuid"`
	Ip        string    `orm:"column(ip);size(64);null" json:"ip"`
	Version   string    `orm:"column(version);size(64);null" json:"version"`
	Size      string    `orm:"column(size);size(64);null" json:"size"`
	Clusterid string    `orm:"column(clusterid);size(64);null" json:"clusterid"`
	Status    bool      `orm:"column(status);null" json:"status"`
	Created   time.Time `orm:"column(created);type(datetime);null" json:"created"`
	Devtype   string    `orm:"column(devtype);size(64);null" json:"devtype"`
}

type Client struct {
	ExportInit
}
