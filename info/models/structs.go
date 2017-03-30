package models

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
}

type Df struct {
	Name      string  `json:"name"`
	Total     float64 `json:"total"`
	Available float64 `json:"available"`
	Used_per  float64 `json:"used_per"`
}
