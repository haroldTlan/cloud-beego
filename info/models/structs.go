package models

import "time"

type Results struct {
	Status string      `json:"status"`
	Ip     string      `json:"ip"`
	Type   string      `json:"type"`
	Result []StoreView `json:"result"`
}

type Statistics struct {
	Exports  []Device `json:"exports"`
	Storages []Device `json:"storages"`
}

type Device struct {
	Info []StoreView `json:"info"`
	Ip   string      `json:"ip"`
}

type StoreView struct {
	Ip        string  `json:"ip"`
	Dev       string  `json:"dev"`
	Dfs       []Df    `json:"df"`
	Cpu       float64 `json:"cpu"`
	Mem       float64 `json:"mem"`
	MemT      float64 `json:"mem_total"`
	Temp      float64 `json:"temp"`
	Write     float64 `json:"write_mb"`
	Read      float64 `json:"read_mb"`
	TimeStamp float64 `json:"timestamp"`
	CacheT    float64 `json:"cache_total"`
	CacheU    float64 `json:"cache_used"`
	W_Vol     float64 `json:"write_vol"`
	R_Vol     float64 `json:"read_vol"`
	Rest      `json:"loc"`
}

type Df struct {
	Name      string  `json:"name"`
	Total     float64 `json:"total"`
	Available float64 `json:"available"`
	Used_per  float64 `json:"used_per"`
}

type Rest struct {
	Disk       []Disks    `json:"disk"`
	Raid       []Raids    `json:"raid"`
	Volume     []Volumes  `json:"volume"`
	Initiator  []Inits    `json:"initiator"`
	Filesystem []Fs       `json:"filesystem"`
	Journal    []Journals `json:"journal"`
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
	Portals []string `json:"portals"`
	Wwn     string   `json:"wwn"`
	Id      string   `json:"id"`
	Volumes []string `json:"volumes"`
	Active  bool     `json:"active_session"`
}

type Initiators struct {
	Portals   string `orm:"column(portals);size(64);pk"`
	Wwn       string `orm:"column(wwn);size(64)"`
	Id_RENAME string `orm:"column(id);size(64)" json:"id"`
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
