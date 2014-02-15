SPECFILE=nitrate.spec

# Support build branch. That is make supports to build package from current git
# branch. If you want to distribute TCMS upon a specific branch, checkout to it
# first, and then issue make.
BUILD_BRANCH=$(shell git branch | grep "^\*" | sed -e "s/\* //")

NAME=$(shell rpm -q --qf "%{NAME}\n" --specfile $(SPECFILE)|head -n1)
VERSION=$(shell rpm -q --qf "%{VERSION}\n" --specfile $(SPECFILE)|head -n1)
RELEASE=$(shell rpm -q --qf "%{RELEASE}\n" --specfile $(SPECFILE)|head -n1)

SRPM=$(NAME)-$(VERSION)-$(RELEASE).src.rpm
TARBALL=nitrate-$(VERSION).tar.bz2
PWD=$(shell pwd)
RPMBUILD_OPTIONS=--nodeps --define "_sourcedir $(PWD)" --define "_srcrpmdir $(PWD)" --define "_rpmdir $(PWD)"

WORK_DIR=/tmp/nitrate-$(VERSION)
SOURCE_DIR = $(WORK_DIR)/nitrate
CODE_REPO=git://git.fedorahosted.org/nitrate.git

default: help
# Target: build a local RPM
local-rpm: $(SRPM)
	echo "$(SRPM)"
	rpmbuild --rebuild $(RPMBUILD_OPTIONS) $(SRPM) || exit 1

# Target for constructing a source RPM:
$(SRPM): $(TARBALL) $(SPECFILE)
	echo "$(TARBALL)"
	rpmbuild -bs $(RPMBUILD_OPTIONS) $(SPECFILE) || exit 1

# Target for constructing a source tarball
# We do not build from the local copy.
# Instead, we always checkout a clean source tree from remote repository.
# This means that we know exactly which version of each file we have in any RPM.
$(TARBALL): Makefile
	@echo "Start to build distribution package upon branch $(BUILD_BRANCH)"
	@rm -rf $(WORK_DIR)
	@rm -f $(TARBALL)
	@mkdir $(WORK_DIR)
	@echo "Getting latest codes from git"
	@cd $(WORK_DIR); git clone -b $(BUILD_BRANCH) $(CODE_REPO)
	# Fixup the version field in the page footer so that it shows the precise
	# RPM version-release:
	@cd $(SOURCE_DIR); sed --in-place -r 's|NITRATE_VERSION|$(VERSION)|' $(SOURCE_DIR)/tcms/templates/tcms_base.html
	@cd $(SOURCE_DIR); python setup.py sdist --formats=bztar
	@cp $(SOURCE_DIR)/dist/$(TARBALL) .

src-rpm: $(SRPM)

# Various targets for debugging the creation of an RPM or SRPM:
# Debug target: stop after the %prep stage
debug-prep: $(TARBALL) $(SPECFILE)
	rpmbuild -bp $(RPMBUILD_OPTIONS) $(SPECFILE) || exit 1

# Debug target: stop after the %build stage
debug-build: $(TARBALL) $(SPECFILE)
	rpmbuild -bc $(RPMBUILD_OPTIONS) $(SPECFILE) || exit 1

# Debug target: stop after the %install stage
debug-install: $(TARBALL) $(SPECFILE)
	rpmbuild -bi $(RPMBUILD_OPTIONS) $(SPECFILE) || exit 1

# Check code convention based on flake8
CHECK_DIRS=manage.py setup.py tcms/wsgi.py tcms/urls.py tcms/settings tcms/apps tcms/integration tcms/report tcms/search tcms/scripts tcms/core
EXCLUDE_DIRS=tcms/core/lib

flake8:
	flake8 $(CHECK_DIRS) --exclude $(EXCLUDE_DIRS)

test:
	python manage.py test

build:
	python setup.py build

install:
	python setup.py install

help:
	@echo 'Usage make [command]'
	@echo ''
	@echo 'Available commands:'
	@echo ''
	@echo '  local-rpm        - Create the binary RPM'
	@echo '  src-rpm          - Create a source RPM'
	@echo '  debug-prep       - Debug nitrate.spec prep'
	@echo '  debug-build      - Debug nitrate.spec build'
	@echo '  debug-install    - Debug nitrate.spec install'
	@echo '  flake8           - Check Python style based on flake8'
	@echo '  test             - Run command: python manage.py test'
	@echo '  build            - Run command: python setup.py build'
	@echo '  install          - Run command: python setup.py install'
	@echo '  help             - Show this help message and exit'
