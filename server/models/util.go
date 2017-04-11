package models

import (
	"fmt"
	"os"
)

func Urandom() string {
	f, _ := os.OpenFile("/dev/urandom", os.O_RDONLY, 0)
	b := make([]byte, 16)
	f.Read(b)
	f.Close()
	uuid := fmt.Sprintf("%x-%x-%x-%x-%x", b[0:4], b[4:6], b[6:8], b[8:10], b[10:])
	return uuid
}

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
}
