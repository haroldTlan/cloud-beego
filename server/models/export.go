package models

import (
	"errors"
	"fmt"
	"reflect"
	"strings"
	_ "time"

	"github.com/astaxie/beego/orm"
)

type Export struct {
	ExportInit `orm:"auto"`
	/*	Id      int       `orm:"column(uid);auto"`
		Uuid    string    `orm:"column(uuid);size(64);null"`
		Ip      string    `orm:"column(ip);size(64);null"`
		Version string    `orm:"column(version);size(64);null"`
		Size    string    `orm:"column(size);size(64);null"`
		Status  int8      `orm:"column(status);null"`
		Created time.Time `orm:"column(created);type(datetime);null"`
		Devtype string    `orm:"column(devtype);size(64);null"`*/
	//Role    string `orm:"column(role);size(64);null"`
	//Virtual string `orm:"column(virtual);size(64);null"`
}

func (t *Export) TableName() string {
	return "export"
}

func init() {
	orm.RegisterModel(new(Export))
}

// AddExport insert a new Export into database and returns
// last inserted Id on success.
func AddExport(m *Export) (id int64, err error) {
	o := orm.NewOrm()
	id, err = o.Insert(m)
	return
}

// GetExportById retrieves Export by Id. Returns error if
// Id doesn't exist
func GetExportById(id int) (v *Export, err error) {
	o := orm.NewOrm()
	//v = &Export{ExportInit{Id: id}}
	v.ExportInit.Id = id
	if err = o.Read(v); err == nil {
		return v, nil
	}
	return nil, err
}

// GetAllExport retrieves all Export matches certain condition. Returns empty list if
// no records exist
func GetAllExport(query map[string]string, fields []string, sortby []string, order []string,
	offset int64, limit int64) (ml []interface{}, err error) {
	o := orm.NewOrm()
	qs := o.QueryTable(new(Export))
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

	var l []Export
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

// UpdateExport updates Export by Id and returns error if
// the record to be updated doesn't exist
func UpdateExportById(m *Export) (err error) {
	o := orm.NewOrm()
	var v Export
	//v := Export{ExportInit{Id: m.Id}}
	v.ExportInit.Id = m.Id

	// ascertain id exists in the database
	if err = o.Read(&v); err == nil {
		var num int64
		if num, err = o.Update(m); err == nil {
			fmt.Println("Number of records updated in database:", num)
		}
	}
	return
}

// DeleteExport deletes Export by Id and returns error if
// the record to be deleted doesn't exist
func DeleteExport(id int) (err error) {
	o := orm.NewOrm()
	var v Export
	v.ExportInit.Id = id

	// ascertain id exists in the database
	if err = o.Read(&v); err == nil {
		var num int64
		//	if num, err = o.Delete(&Export{ExportInit{Id: id}}); err == nil {
		if num, err = o.Delete(v); err == nil {
			fmt.Println("Number of records deleted in database:", num)
		}
	}
	return
}
