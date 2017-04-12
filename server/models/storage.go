package models

import (
	"errors"
	"fmt"
	"reflect"
	"strings"
	_ "time"

	"github.com/astaxie/beego/orm"
)

type Storage struct {
	/*	Id      int       `orm:"column(uid);auto"`
		Uuid    string    `orm:"column(uuid);size(64);null"`
		Ip      string    `orm:"column(ip);size(64);null"`
		Version string    `orm:"column(version);size(64);null"`
		Size    string    `orm:"column(size);size(64);null"`
		Master  string    `orm:"column(master);size(64);null"`
		Cid     int       `orm:"column(cid);null"`
		Sid     int       `orm:"column(sid);null"`
		Slot    string    `orm:"column(slot);size(64);null"`
		Status  int8      `orm:"column(status);null"`
		Created time.Time `orm:"column(created);type(datetime);null"`
		Devtype string    `orm:"column(devtype);size(64);null"`*/
	ExportInit
}

func (t *Storage) TableName() string {
	return "storage"
}

func init() {
	orm.RegisterModel(new(Storage))
}

// AddStorage insert a new Storage into database and returns
// last inserted Id on success.
func AddStorage(m *Storage) (id int64, err error) {
	o := orm.NewOrm()
	id, err = o.Insert(m)
	return
}

// GetStorageById retrieves Storage by Id. Returns error if
// Id doesn't exist
func GetStorageById(id int) (v *Storage, err error) {
	o := orm.NewOrm()
	//v = &Storage{Id: id}
	v.ExportInit.Id = id
	if err = o.Read(v); err == nil {
		return v, nil
	}
	return nil, err
}

// GetAllStorage retrieves all Storage matches certain condition. Returns empty list if
// no records exist
func GetAllStorage(query map[string]string, fields []string, sortby []string, order []string,
	offset int64, limit int64) (ml []interface{}, err error) {
	o := orm.NewOrm()
	qs := o.QueryTable(new(Storage))
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

	var l []Storage
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

// UpdateStorage updates Storage by Id and returns error if
// the record to be updated doesn't exist
func UpdateStorageById(m *Storage) (err error) {
	o := orm.NewOrm()
	//v := Storage{Id: m.Id}
	var v Storage
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

// DeleteStorage deletes Storage by Id and returns error if
// the record to be deleted doesn't exist
func DeleteStorage(id int) (err error) {
	o := orm.NewOrm()
	//v := Storage{Id: id}
	var v Storage
	v.ExportInit.Id = id
	// ascertain id exists in the database
	if err = o.Read(&v); err == nil {
		var num int64
		//	if num, err = o.Delete(&Storage{Id: id}); err == nil {
		if num, err = o.Delete(v); err == nil {
			fmt.Println("Number of records deleted in database:", num)
		}
	}
	return
}
