package models

import (
	"fmt"
	"reflect"
	"strings"

	"github.com/astaxie/beego/orm"
)

type Threshhold struct {
	Id      int     `orm:"column(uid);auto" json:"uid"`
	Dev     string  `orm:"column(dev);size(64)" json:"dev"`
	Type    string  `orm:"column(type);size(64)" json:"type"`
	Warning float64 `orm:"column(warning)" json:"warning"`
	Normal  float64 `orm:"column(normal)" json:"normal"`
	Name    string  `orm:"column(name);size(64)" json:"name"`
}

func (t *Threshhold) TableName() string {
	return "threshhold"
}

func init() {
	orm.RegisterModel(new(Threshhold))
}

// AddThreshhold insert a new Threshhold into database and returns
// last inserted Id on success.
func AddThreshhold(m *Threshhold) (id int64, err error) {
	o := orm.NewOrm()
	id, err = o.Insert(m)
	return
}

// GetThreshholdById retrieves Threshhold by Id. Returns error if
// Id doesn't exist
func GetThreshholdById(id int) (v *Threshhold, err error) {
	o := orm.NewOrm()
	v = &Threshhold{Id: id}
	if err = o.Read(v); err == nil {
		return v, nil
	}
	return nil, err
}

// GetAllThreshhold retrieves all Threshhold matches certain condition. Returns empty list if
// no records exist
func GetAllThreshhold(query map[string]string, fields []string, sortby []string, order []string,
	offset int64, limit int64) (ml []interface{}, err error) {
	o := orm.NewOrm()
	qs := o.QueryTable(new(Threshhold))
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

	var l []Threshhold
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

// UpdateThreshhold updates Threshhold by Id and returns error if
// the record to be updated doesn't exist
func UpdateThreshholdById(uid int, normal, warning float64) (err error) {
	o := orm.NewOrm()
	v := Threshhold{Id: uid}
	// ascertain id exists in the database
	if err = o.Read(&v); err == nil {
		v.Normal = normal
		v.Warning = warning
		fmt.Println(v)
		if _, err = o.Update(&v); err == nil {
		}
	}
	return
}

// DeleteThreshhold deletes Threshhold by Id and returns error if
// the record to be deleted doesn't exist
func DeleteThreshhold(id int) (err error) {
	o := orm.NewOrm()
	v := Threshhold{Id: id}
	// ascertain id exists in the database
	if err = o.Read(&v); err == nil {
		var num int64
		if num, err = o.Delete(&Threshhold{Id: id}); err == nil {
			fmt.Println("Number of records deleted in database:", num)
		}
	}
	return
}
