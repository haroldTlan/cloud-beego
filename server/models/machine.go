package models

import (
	"errors"
	"fmt"
	"reflect"
	"regexp"
	"strings"
	"time"

	"github.com/astaxie/beego/orm"
)

type Machine struct {
	Id        int       `orm:"column(uid);auto" json:"Uid"`
	Uuid      string    `orm:"column(uuid);size(64);null"`
	Ip        string    `orm:"column(ip);size(64);null"`
	Slotnr    int       `orm:"column(slotnr);null"`
	Created   time.Time `orm:"column(created);type(datetime);null"`
	Devtype   string    `orm:"column(devtype);size(64);null"`
	Status    bool      `orm:"column(status);null"`
	Role      string    `orm:"column(role);size(64);null"`
	Clusterid string    `orm:"column(clusterid);size(64);null"`
}

func (t *Machine) TableName() string {
	return "machine"
}

func init() {
	orm.RegisterModel(new(Machine))
}

// AddMachine insert a new Machine into database and returns
// last inserted Id on success.
func AddMachine(ip, devtype, role, cluster string, slotnr int) (err error) {
	o := orm.NewOrm()

	if m, _ := regexp.MatchString("^[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}$", ip); !m {
		err = errors.New("not validate IP address")
		AddLog(err)
		return
	} else if exist := o.QueryTable("machine").Filter("ip", ip).Filter("devtype", devtype).Exist(); exist {
		err = errors.New("Ip address already exits")
		AddLog(err)
		return
	} else if len(devtype) == 0 {
		err = errors.New("devtype type not set")
		AddLog(err)
		return
	} else if devtype != "client" || devtype != "storage" || devtype != "export" {
		err = errors.New("not validate devtype")
		AddLog(err)
		return
	}

	var m Machine
	uran := Urandom()
	uuid := uran + "zip" + strings.Join(strings.Split(ip, "."), "")
	m.Uuid = uuid
	m.Ip = ip
	m.Devtype = devtype
	m.Slotnr = slotnr
	m.Created = time.Now()
	m.Status = true
	//m.Role = role
	//.Clusterid = cluster

	if _, err = o.Insert(&m); err != nil {
		AddLog(err)
		return
	}
	return
}

// GetAllMachine retrieves all Machine matches certain condition. Returns empty list if
// no records exist
func GetAllMachine(query map[string]string, fields []string, sortby []string, order []string,
	offset int64, limit int64) (ml []interface{}, err error) {
	ml = make([]interface{}, 0)
	o := orm.NewOrm()
	qs := o.QueryTable(new(Machine))
	// query k=v
	for k, v := range query {
		// rewrite dot-notation to Object__Attribute
		k = strings.Replace(k, ".", "__", -1)
		if strings.Contains(k, "isnull") {
			qs = qs.Filter(k, (v == "true" || v == "1"))
		} else {
			qs = qs.Filter(k, v)
		}
	}
	// order by:
	var sortFields []string
	if len(sortby) != 0 {
		if len(sortby) == len(order) {
			// 1) for each sort field, there is an associated order
			for i, v := range sortby {
				orderby := ""
				if order[i] == "desc" {
					orderby = "-" + v
				} else if order[i] == "asc" {
					orderby = v
				} else {
					return nil, errors.New("Error: Invalid order. Must be either [asc|desc]")
				}
				sortFields = append(sortFields, orderby)
			}
			qs = qs.OrderBy(sortFields...)
		} else if len(sortby) != len(order) && len(order) == 1 {
			// 2) there is exactly one order, all the sorted fields will be sorted by this order
			for _, v := range sortby {
				orderby := ""
				if order[0] == "desc" {
					orderby = "-" + v
				} else if order[0] == "asc" {
					orderby = v
				} else {
					return nil, errors.New("Error: Invalid order. Must be either [asc|desc]")
				}
				sortFields = append(sortFields, orderby)
			}
		} else if len(sortby) != len(order) && len(order) != 1 {
			return nil, errors.New("Error: 'sortby', 'order' sizes mismatch or 'order' size is not 1")
		}
	} else {
		if len(order) != 0 {
			return nil, errors.New("Error: unused 'order' fields")
		}
	}

	var l []Machine
	qs = qs.OrderBy(sortFields...)
	if _, err = qs.Limit(limit, offset).All(&l, fields...); err == nil {
		if len(fields) == 0 {
			for _, v := range l {
				ml = append(ml, v)
			}
		} else {
			// trim unused fields
			for _, v := range l {
				m := make(map[string]interface{})
				val := reflect.ValueOf(v)
				for _, fname := range fields {
					m[fname] = val.FieldByName(fname).Interface()
				}
				ml = append(ml, m)
			}
		}
		return ml, nil
	}

	return nil, err
}

// UpdateMachine updates Machine by Id and returns error if
// the record to be updated doesn't exist
func UpdateMachineById(m *Machine) (err error) {
	o := orm.NewOrm()
	v := Machine{Id: m.Id}
	// ascertain id exists in the database
	if err = o.Read(&v); err == nil {
		var num int64
		if num, err = o.Update(m); err == nil {
			fmt.Println("Number of records updated in database:", num)
		}
	}
	return
}

// DeleteMachine deletes Machine by Id and returns error if
// the record to be deleted doesn't exist
func DeleteMachine(uuid string) (err error) {
	o := orm.NewOrm()
	// ascertain id exists in the database
	if exist := o.QueryTable("machine").Filter("uuid", uuid).Exist(); exist {
		if _, err = o.QueryTable("machine").Filter("uuid", uuid).Delete(); err != nil {
			AddLog(err)
			return
		}
	} else {
		err = errors.New("uuid not exits")
		AddLog(err)
		return
	}
	return nil
}
