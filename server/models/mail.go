package models

import (
	"fmt"
	"reflect"
	"strconv"
	"strings"

	"github.com/astaxie/beego/orm"
)

type Mail struct {
	Id      int    `orm:"column(uid);auto" json:"uid"`
	Address string `orm:"column(address);size(64);null" json:"address"`
	Level   int    `orm:"column(level);null" json:"level"`
	Ttl     int    `orm:"column(ttl);null" json:"ttl"`
}

func (t *Mail) TableName() string {
	return "mail"
}

func init() {
	orm.RegisterModel(new(Mail))
}

// AddMail insert a new Mail into database and returns
// last inserted Id on success.
func AddMail(address, l, t string) (err error) {
	o := orm.NewOrm()
	var m Mail
	m.Address = address
	level, err := strconv.Atoi(l)
	if err != nil {
		return err
	}
	m.Level = level
	ttl, err := strconv.Atoi(t)
	if err != nil {
		return err
	}
	m.Ttl = ttl

	_, err = o.Insert(&m)
	return
}

// GetAllMail retrieves all Mail matches certain condition. Returns empty list if
// no records exist
func GetAllMail(query map[string]string, fields []string, sortby []string, order []string,
	offset int64, limit int64) (ml []interface{}, err error) {
	o := orm.NewOrm()
	ml = make([]interface{}, 0)
	qs := o.QueryTable(new(Mail))
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
					return nil, fmt.Errorf("Error: Invalid order. Must be either [asc|desc]")
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
					return nil, fmt.Errorf("Error: Invalid order. Must be either [asc|desc]")
				}
				sortFields = append(sortFields, orderby)
			}
		} else if len(sortby) != len(order) && len(order) != 1 {
			return nil, fmt.Errorf("Error: 'sortby', 'order' sizes mismatch or 'order' size is not 1")
		}
	} else {
		if len(order) != 0 {
			return nil, fmt.Errorf("Error: unused 'order' fields")
		}
	}

	var l []Mail
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
	return ml, err
}

// UpdateMail updates Mail by Id and returns error if
// the record to be updated doesn't exist
func UpdateMailById(id, l, ttl int) (err error) {
	o := orm.NewOrm()
	v := Mail{Id: id}
	// ascertain id exists in the database

	if err = o.Read(&v); err == nil {
		fmt.Println(v)
		v.Level = l
		v.Ttl = ttl
		fmt.Printf("%+v", v)
		if _, err = o.Update(&v); err == nil {
		}
	}

	return
}

// DeleteMail deletes Threshhold by Id and returns error if
// the record to be deleted doesn't exist
func DeleteMail(uid string) (err error) {
	o := orm.NewOrm()

	id, err := strconv.Atoi(uid)
	if err != nil {
		return err
	}

	v := Mail{Id: id}
	// ascertain id exists in the database
	if err = o.Read(&v); err == nil {
		_, err = o.Delete(&Mail{Id: id})
	}
	return
}

/*
	o := orm.NewOrm()
	v := Mail{Id: m.Id}
	// ascertain id exists in the database
	if err = o.Read(&v); err == nil {
		var num int64
		if num, err = o.Update(m); err == nil {
			fmt.Println("Number of records updated in database:", num)
		}
	}
	return
}*/
