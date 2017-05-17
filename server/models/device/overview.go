package device

import (
	"aserver/models/util"
	"github.com/astaxie/beego/orm"
)

type View struct {
	NumOfDisks      int64
	NumOfRaids      int64
	NumOfVols       int64
	NumOfFs         int64
	NumOfInitiators int64
}

// GetOverViews retrieves overviews matches certain condition.
// Returns empty list if no records exist.
func GetOverViews() (views View, err error) {
	o := orm.NewOrm()

	disks_num, err := o.QueryTable(new(Disks)).Count()
	if err != nil {
		util.AddLog(err)
	}

	raids_num, err := o.QueryTable(new(Raids)).Count()
	if err != nil {
		util.AddLog(err)
	}

	vols_num, err := o.QueryTable(new(Volumes)).Count()
	if err != nil {
		util.AddLog(err)
	}

	fs_num, err := o.QueryTable(new(Fs)).Count()
	if err != nil {
		util.AddLog(err)
	}

	inits_num, err := o.QueryTable(new(Initiators)).Count()
	if err != nil {
		util.AddLog(err)
	}

	views = View{NumOfDisks: disks_num, NumOfRaids: raids_num, NumOfVols: vols_num, NumOfFs: fs_num, NumOfInitiators: inits_num}
	return

}
