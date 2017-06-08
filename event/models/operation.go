package models

import (
	"event/models/util"
	"github.com/astaxie/beego/orm"
)

// Setting Client
func ClientUpdate(ip, event string, status bool) (err error) {
	o := orm.NewOrm()

	var c Client
	if err = o.QueryTable("client").Filter("ip", ip).One(&c); err != nil {
		util.AddLog(err)
		return
	}

	// update client's status
	if event == "cmd.client.add" && status {
		c.Status = true
		if _, err = o.Update(&c); err != nil {
			util.AddLog(err)
			return
		}
	}

	// remove delete client or TODO make client's status false
	if event == "cmd.client.remove" && status {
		if _, err = o.QueryTable(new(Client)).Filter("ip", ip).Delete(); err != nil {
			util.AddLog(err)
			return
		}
	}
	return
}

// Setting Storage
func StorageUpdate(ip string, status int, event string) (err error) {
	o := orm.NewOrm()

	var c Cluster
	var s Storage

	// get cluster's status and update
	if err = o.QueryTable("storage").Filter("ip", ip).One(&s); err != nil {
		util.AddLog(err)
		return
	}
	if err = o.QueryTable("cluster").Filter("uuid", s.Clusterid).One(&c); err != nil {
		util.AddLog(err)
		return
	}

	// TODO not finished
	// 1,0,1,1  0,1,1,1
	if event == "cmd.storage.build" {
		c.Store = (status == 0)
	} else {
		if status == 0 {
			c.Store = false
		}
	}

	// update storage's status
	if _, err = o.Update(&c); err != nil {
		util.AddLog(err)
		return
	}

	return
}

// Use Global to collect event
func RpcSetting(resEvent string, values map[string]interface{}) (count float64) {
	// GUI's resciver name
	// clientEvent := "cmd.client.change"

	// True or False's counts
	success, err := 0, 0
	// Failed reason
	errMsg := ""

	// base event infos
	ip := values["ip"].(string)
	id := values["id"].(string)
	event := values["event"].(string)
	status := values["status"].(bool)
	detail := values["detail"].(string)

	if status {
		success = 1
	} else {
		err = 1
		errMsg = detail
	}

	if _, ok := NsqEvents[id]; ok {
		// more then the first time
		_err := NsqEvents[id].ErrCount + err
		_success := NsqEvents[id].Success + success
		_count := NsqEvents[id].Count + 1
		_msg := NsqEvents[id].ErrorMsg

		if !status {
			_msg = append(_msg, ErrMsg{Ip: ip, Msg: errMsg, SetType: event})
		}

		NsqEvents[id] = Setting{Count: _count, Event: resEvent, ErrCount: _err, Success: _success, ErrorMsg: _msg}

	} else {
		// the first time
		msg := make([]ErrMsg, 0)
		// when failed, add error message
		if !status {
			msg = []ErrMsg{ErrMsg{Ip: ip, Msg: errMsg, SetType: event}}
		}

		NsqEvents[id] = Setting{Count: 1, Event: resEvent, ErrCount: err, Success: success, ErrorMsg: msg}
	}

	count = float64(NsqEvents[id].Count)
	return
}

// ordinary event
// Insert table emergency
// special event to do special operation
func RefreshOverViews(ip, event string) (err error) {
	if err = InsertEmergencys(event, ip); err != nil {
		util.AddLog(err)
		return
	}

	/*
		if err := MulAttention(ip, event); err != nil { //mul email sending TODO
			return err
		}*/

	return nil
}
