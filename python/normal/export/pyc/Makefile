DIST_DIR = dist
DIST_TAR = dist.tar.gz
PY_FILES = $(wildcard *.py)
SHELL_FILES = $(wildcard *.sh)
UTILS_FILES = change_linux_admin_passwd device_status zonion_log
MISC_FILES = speedio.conf Makefile
PREINIT_DIR = preinit

.PHONY: $(DIST_DIR)

dist:
	if [ -d $(DIST_DIR) ]; then rm $(DIST_DIR) -rf; fi;
	mkdir $(DIST_DIR)
	cp $(PY_FILES) $(DIST_DIR)
	cp $(SHELL_FILES) $(DIST_DIR)
	cp $(UTILS_FILES) $(DIST_DIR)
	cp $(MISC_FILES) $(DIST_DIR)
	cp $(PREINIT_DIR) $(DIST_DIR) -r
	python -m compileall $(DIST_DIR)
	cd $(DIST_DIR); chmod +x *.pyc *.sh $(UTILS_FILES)
	cd $(DIST_DIR); rm *.py -rf; rm $(PREINIT_DIR)/*.py -rf
	cp lm.py $(DIST_DIR)
	cp lm_24_24.py $(DIST_DIR)
	cp version $(DIST_DIR)
	cp scripts $(DIST_DIR) -rf
	rm $(DIST_DIR)/lm.pyc -rf

clean:
	if [ -d $(DIST_DIR) ]; then rm $(DIST_DIR) -rf; fi;
	-rm *.pyc -rf

install:
	mv ../`basename $(PWD)` ../speedio
	mv create_lw_files.pyc ../command
	mv version ../
	-rm ../command/poweroff.sh
	-rm ../command/poweroff.pyc
	cp poweroff.pyc ../command
	-rm ../command/reboot.sh
	-rm ../command/reboot.pyc
	cp reboot.pyc ../command
	-rm /usr/bin/device_status -rf
	ln -s `pwd`/device_status /usr/bin/device_status
	-rm /usr/bin/zonion_log -rf
	ln -s `pwd`/zonion_log /usr/bin/zonion_log
	-rm Makefile

tar: dist
	tar czf $(DIST_TAR) $(DIST_DIR)
	if [ -d $(DIST_DIR) ]; then rm $(DIST_DIR) -rf; fi;
