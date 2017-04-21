package models

import (
	"aserver/models/device"
	"fmt"
	"github.com/astaxie/beego/context"
	"github.com/astaxie/beego/orm"
	_ "net/http"
	"strconv"
	"time"
)

type ResEmergency struct {
	Uid            int       `json:"uid"`
	Created        time.Time `orm:"index" json:"created"`
	Unix           int64     `json:"unix"`
	Ip             string    `json:"ip"`
	Event          string    `json:"event"`
	MachineId      string    `json:"machineId"`
	Devtype        string    `json:"devtype"`
	Level          string    `json:"level"`
	ChineseMessage string    `json:"chinese_message"`
	Status         bool      `json:"status"`
}

func GetJournals() (es []ResEmergency, err error) {
	o := orm.NewOrm()
	es = make([]ResEmergency, 0)
	emergencys := make([]device.Emergency, 0) //TODO emergency
	if _, err = o.QueryTable(new(device.Emergency)).Filter("status", 0).All(&emergencys); err != nil {
		return
	}

	for _, i := range emergencys {
		var one device.Machine
		if _, err = o.QueryTable(new(device.Machine)).Filter("ip", i.Ip).All(&one); err != nil {
			return
		}

		var jour ResEmergency
		jour.Uid = i.Id
		jour.Created = i.CreatedAt
		jour.Unix = i.CreatedAt.Unix()
		jour.Event = i.Event
		jour.Level = i.Level
		jour.ChineseMessage = i.ChineseMessage
		jour.Status = i.Status
		jour.MachineId = one.Uuid
		jour.Ip = one.Ip
		jour.Devtype = one.Devtype
		es = append(es, jour)
	}
	return
}

func Datatables(aColumns []string, Input *context.BeegoInput) ([][]interface{}, int64, int64) {
	/*
			   Paging  分页请求
		       iDisplayStart  起始数目
		       iDisplayLength 每页显示数量
	*/
	iDisplayStart, _ := strconv.Atoi(Input.Query("iDisplayStart"))
	iDisplayLength, _ := strconv.Atoi(Input.Query("iDisplayLength"))

	//  * Filtering  快速过滤器
	cond := orm.NewCondition()
	if len(Input.Query("sSearch")) > 0 {
		for i := 0; i < len(aColumns); i++ {
			cond = cond.Or(aColumns[i]+"__icontains", Input.Query("sSearch"))
		}
	}

	for i := 0; i < len(aColumns); i++ {
		if Input.Query("bSearchable_"+strconv.Itoa(i)) == "true" && len(Input.Query("sSearch_"+strconv.Itoa(i))) > 0 {
			cond = cond.And(aColumns[i]+"__icontains", Input.Query("sSearch"))
		}
	}

	maps, b, c := AllLocalJournals(iDisplayStart, iDisplayLength, cond)

	var output = make([][]interface{}, len(maps))
	for i, m := range maps {
		for _, v := range aColumns {
			if v == "CreatedAt" {
				fmt.Printf("%+v", m[v])
				output[i] = append(output[i], m[v].(time.Time).Format("2006-01-02 15:04:05"))
			} else {
				output[i] = append(output[i], m[v])
			}
		}
	}
	return output, b, c
}

func AllLocalJournals(start, length int, cond *orm.Condition) ([]orm.Params, int64, int64) {
	o := orm.NewOrm()
	ones := make([]orm.Params, 0)

	qs_emergency := o.QueryTable("emergency")
	qs_emergency = qs_emergency.OrderBy("-" + "uid")
	counts, _ := qs_emergency.Count()
	qs_emergency = qs_emergency.Limit(length, start)
	qs_emergency = qs_emergency.SetCond(cond)
	qs_emergency.Values(&ones)
	count, _ := qs_emergency.Count()

	return ones, count, counts
}
