package ansible

import (
	"aserver/models/util"

	"bytes"
	"fmt"
	"os/exec"
)

func Active(act bool) (err error) {
	var cmd *exec.Cmd
	cmdT := make([]string, 0)
	//  cmdT = append(cmdArgs,"ansible")
	cmdT = append(cmdT, "gateway")
	cmdT = append(cmdT, "-m", "command")
	cmdT = append(cmdT, "-a", "service packetbeat start")

	cmdF := make([]string, 0)
	//  cmdT = append(cmdArgs,"ansible")
	cmdF = append(cmdF, "gateway")
	cmdF = append(cmdF, "-m", "command")
	cmdF = append(cmdF, "-a", "service packetbeat stop")

	if act {
		cmd = exec.Command("ansible", cmdT...)
	} else {
		cmd = exec.Command("ansible", cmdF...)

	}
	cmdOutput := &bytes.Buffer{}
	// Attach buffer to command
	cmd.Stdout = cmdOutput

	// Execute command
	err = cmd.Run()
	if err != nil {
		util.AddLog(err)
	}
	outs := cmdOutput.Bytes()
	fmt.Println(outs)
	return
}
