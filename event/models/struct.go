package models

import (
	"time"
)

type Setting struct {
	Event    string   `json:"event"`
	Count    int      `json:"count"`
	ErrCount int      `json:"errCount"`
	Success  int      `json:"success"`
	ErrorMsg []ErrMsg `json:"errorMsg"`
}

type ErrMsg struct {
	Ip      string `json:"ip"`
	Msg     string `json:"msg"`
	SetType string `json:"type"`
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

type Machine struct {
	Uid     int       `orm:"pk" json:"uid"`
	Uuid    string    `json:"uuid"`
	Ip      string    `json:"ip"`
	Devtype string    `json:"ip"`
	Slotnr  int       `json:"slotnr"`
	Created time.Time `orm:"index" json:"created"`
	Status  bool      `json:"status"`
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
