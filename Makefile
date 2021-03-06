HAVE_PYINSTALLER = $(shell which pyinstaller 2>/dev/null && echo 0 || echo 1)
VERSION = $(shell grep VERSION\  omwrm/omwrm.py | awk -F\" '{ print  $$2 }')

.DEFAULT_GOAL:= install

all: install-pip-pkgs clean test exe install

check_pyinstaller:
ifeq ($(HAVE_PYINSTALLER), 1)
	@echo PyInstaller is required to build an executable!
	@exit 1
endif

clean:
	@/bin/rm -fr build dist *.egg-info ./omwrm/__pycache__ ./omwrm/build ./omwrm/dist \
	openmw-rm-* openmw-rm_*.sha256sum ./omwrm/openmw-rm.spec ./__pycache__

exe: check_pyinstaller
	@cd omwrm && \
	~/.local/bin/pyinstaller --name openmw-rm --onefile omwrm.py && \
	cd .. && \
	mv omwrm/dist/openmw-rm openmw-rm-$(VERSION) && \
	sha256sum openmw-rm-$(VERSION) > openmw-rm_$(VERSION).sha256sum && \
	echo && echo BUILT: openmw-rm-$(VERSION) AND openmw-rm_$(VERSION).sha256sum

install:
	@pip3 install --compile --upgrade --user .

install-pip-pkgs:
	@pip3 install --user pyinstaller

test:
	@python3 test.py
