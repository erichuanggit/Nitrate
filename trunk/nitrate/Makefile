SPECFILE=nitrate.spec
# FIXME: this varialbe is for install and install-data. If remove them, also
# remove this one.
PREFIX=/usr

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
RPMBUILD_OPTIONS=--nodeps --define "_sourcedir $(PWD)" --define "_srcrpmdir $(PWD)"

WORK_DIR=/tmp/nitrate-$(VERSION)
SOURCE_DIR = $(WORK_DIR)/nitrate/trunk/
CODE_REPO=git://git.fedorahosted.org/nitrate.git

# Target: build a local RPM
local-rpm: $(SRPM)
	echo "$(SRPM)"
	rpmbuild --rebuild $(SRPM) || exit 1

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
	@cd $(SOURCE_DIR); sed --in-place -r 's|NITRATE_VERSION|$(VERSION)|' $(SOURCE_DIR)/nitrate/templates/tcms_base.html
	@cd $(SOURCE_DIR); mv nitrate nitrate-${VERSION}
	@cd $(SOURCE_DIR); tar --bzip2 --exclude .git -cSpf $(TARBALL) nitrate-${VERSION}
	@cp $(SOURCE_DIR)/$(TARBALL) .

src-rpm: $(SRPM)

# Shortcut target for building in brew:
brew: $(SRPM)
	brew build --nowait dist-5E-eso $(SRPM)

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

pylint:
	PYTHONPATH=.. pylint tcms

test:
	python manage.py test

# FIXME: remove install and install-data?
install: $(install-data)
	python setup.py install -O1 --skip-build --root ${PREFIX}

install-data:
	@mkdir -pv ${PREFIX}/share/${NAME}
	for d in contrib templates media; do \
		cp -rv $$d ${PREFIX}/share/${NAME}; \
	done

# FIXME:
# Things to add:
#   - unit tests
