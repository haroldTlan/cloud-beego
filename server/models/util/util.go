package util

import (
	"fmt"
	"github.com/astaxie/beego/logs"
	"os"
	"regexp"
	"runtime"
)

func Urandom() string {
	f, _ := os.OpenFile("/dev/urandom", os.O_RDONLY, 0)
	l := make([]byte, 16)
	f.Read(l)
	f.Close()
	uuid := fmt.Sprintf("%x-%x-%x-%x-%x", l[0:4], l[4:6], l[6:8], l[8:10], l[10:])
	return uuid
}

//logs
func AddLog(err interface{}, v ...interface{}) {
	if _, ok := err.(error); ok {
		pc, _, line, _ := runtime.Caller(1)
		logs.Error("[Server] ", runtime.FuncForPC(pc).Name(), line, v, err)
	} else {
		logs.Info("[Server] ", err)
	}
}

func JudgeIp(ip string) (err error) {
	if m, _ := regexp.MatchString("^[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}$", ip); !m {
		err = fmt.Errorf("not validate IP address")
		AddLog(err)
		return
	}
	return
}

/*
func NewResponse(status string, detail interface{}) map[string]interface{} {
	o := make(map[string]interface{})
	o["status"] = status
	if detail != nil {
		switch v := detail.(type) {
		case error:
			o["errcode"] = 1
			o["description"] = v.Error()
		default:
			o["detail"] = v
		}
	}
	return o
}*/
