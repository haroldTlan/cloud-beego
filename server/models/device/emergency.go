package device

import (
	"errors"
	"fmt"
	"reflect"
	"strings"
	"time"

	"github.com/astaxie/beego/orm"
)

type Emergency struct {
	Id             int       `orm:"column(uid);auto"`
	Level          string    `orm:"column(level);size(50);null"`
	Message        string    `orm:"column(message);size(200);null"`
	ChineseMessage string    `orm:"column(chinese_message);size(200);null"`
	UpdatedAt      time.Time `orm:"column(updated_at);type(datetime);null"`
	CreatedAt      time.Time `orm:"column(created_at);type(datetime);null"`
	Ip             string    `orm:"column(ip);size(64);null"`
	Event          string    `orm:"column(event);size(64);null"`
	Status         bool      `orm:"column(status);null"`
}

func (t *Emergency) TableName() string {
	return "emergency"
}

func init() {
	orm.RegisterModel(new(Emergency))
}

// AddEmergency insert a new Emergency into database and returns
// last inserted Id on success.
func AddEmergency(m *Emergency) (id int64, err error) {
	o := orm.NewOrm()
	id, err = o.Insert(m)
	return
}

// GetEmergencyById retrieves Emergency by Id. Returns error if
// Id doesn't exist
func GetEmergencyById(id int) (v *Emergency, err error) {
	o := orm.NewOrm()
	v = &Emergency{Id: id}
	if err = o.Read(v); err == nil {
		return v, nil
	}
	return nil, err
}

// GetAllEmergency retrieves all Emergency matches certain condition. Returns empty list if
// no records exist
func GetAllEmergency(query map[string]string, fields []string, sortby []string, order []string,
	offset int64, limit int64) (ml []interface{}, err error) {
	o := orm.NewOrm()
	qs := o.QueryTable(new(Emergency))
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

	var l []Emergency
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

// UpdateEmergency updates Emergency by Id and returns error if
// the record to be updated doesn't exist
func UpdateEmergencyById(m int) (err error) {
	o := orm.NewOrm()
	v := Emergency{Id: m}
	// ascertain id exists in the database
	if err = o.Read(&v); err == nil {
		fmt.Printf("%+v", v)
		v.Status = true
		if _, err = o.Update(&v); err != nil {
			fmt.Printf("%+v", err)
			return
		}
	}
	return
}

// DeleteEmergency deletes Emergency by Id and returns error if
// the record to be deleted doesn't exist
func DeleteEmergency(id int) (err error) {
	o := orm.NewOrm()
	v := Emergency{Id: id}
	// ascertain id exists in the database
	if err = o.Read(&v); err == nil {
		var num int64
		if num, err = o.Delete(&Emergency{Id: id}); err == nil {
			fmt.Println("Number of records deleted in database:", num)
		}
	}
	return
}