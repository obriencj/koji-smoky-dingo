# Sorry that this Makefile is a bit of a disaster.


PYTHON ?= $(shell which python3 python 2>/dev/null | head -n1)
PYTHON := $(PYTHON)

TOX ?= $(shell which tox 2>/dev/null | head -n1)
TOX := $(TOX)


PROJECT := $(shell $(PYTHON) ./setup.py --name)
VERSION := $(shell $(PYTHON) ./setup.py --version)

ARCHIVE := $(PROJECT)-$(VERSION).tar.gz


# for hosting local docs preview
PORT ?= 8900


define checkfor
	@if ! which $(1) >/dev/null 2>&1 ; then \
		echo $(1) "is required, but not available" 1>&2 ; \
		exit 1 ; \
	fi
endef


##@ Basic Targets

default: quick-test	## Runs the quick-test target


help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)


report-python:
	@echo "Using python" $(PYTHON)
	@$(PYTHON) -VV


##@ Local Build and Install

build: clean-built report-python flake8	## Produces a wheel using the default system python
	@$(TOX) -qe build


install: build	## Installs using the default python for the current user
ifeq ($(UID),"0")
	@$(PYTHON) -B -m pip.__main__ \
		install -I --no-deps \
		dist/$(PROJECT)-$(VERSION)-py3-none-any.whl
else
	@$(PYTHON) -B -m pip.__main__ \
		install -I --no-deps --user \
		dist/$(PROJECT)-$(VERSION)-py3-none-any.whl
	@mkdir -p ~/.koji/plugins
	@rm -f ~/.koji/plugins/kojismokydingometa.py
	@ln -s `$(PYTHON) -c 'import koji_cli_plugins.kojismokydingometa as ksdm ; print(ksdm.__file__);'` ~/.koji/plugins/kojismokydingometa.py
endif


##@ Cleanup

purge:	clean
	@rm -rf .eggs .tox .mypy_cache


tidy:	## Removes stray eggs and .pyc files
	@rm -rf *.egg-info
	@$(call checkfor,find)
	@find -H . \
		\( -iname '.tox' -o -iname '.eggs' -prune \) -o \
		\( -type d -iname '__pycache__' -exec rm -rf {} + \) -o \
		\( -type f -iname '*.pyc' -exec rm -f {} + \)


clean-built:
	@rm -rf build/* dist/*
	@if [ -f ./"$(ARCHIVE)" ] ; then rm -f ./"$(ARCHIVE)" ; fi


clean: clean-built tidy	## Removes built content, test logs, coverage reports
	@rm -rf .coverage* bandit.sarif htmlcov/* logs/*


##@ Containerized RPMs

packaging-build: $(ARCHIVE)	## Launches all containerized builds
	@./tools/launch-build.sh


packaging-test: packaging-build	## Launches all containerized tests
	@rm -rf logs/*
	@./tools/launch-test.sh


##@ Testing

test: clean requires-tox	## Launches tox
	@$(TOX) -q


bandit:	requires-tox	## Launches bandit via tox
	@$(TOX) -qe bandit


flake8:	requires-tox	## Launches flake8 via tox
	@$(TOX) -qe flake8


mypy:	requires-tox	## Launches mypy via tox
	@$(TOX) -qe mypy


coverage: requires-tox	## Collects coverage report
	@$(TOX) -qe coverage


quick-test: requires-tox flake8	## Launches nosetest using the default python
	@$(TOX) -qe quicktest


##@ RPMs
srpm: $(ARCHIVE)	## Produce an SRPM from the archive
	@$(call checkfor,rpmbuild)
	@rpmbuild \
		--define "_srcrpmdir dist" \
		--define "dist %{nil}" \
		-ts "$(ARCHIVE)"


rpm: $(ARCHIVE)		## Produce an RPM from the archive
	@$(call checkfor,rpmbuild)
	@rpmbuild --define "_rpmdir dist" -tb "$(ARCHIVE)"


archive: $(ARCHIVE)	## Extracts an archive from the current git commit


$(ARCHIVE):	requires-git
	@git archive HEAD --prefix "$(PROJECT)-$(VERSION)/" \
	   --format tar.gz -o $@


##@ Documentation

docs: clean-docs requires-tox docs/overview.rst	## Build sphinx docs
	@$(TOX) -qe sphinx


overview: docs/overview.rst  ## rebuilds the overview from README.md


docs/overview.rst: README.md
	@$(call checkfor,pandoc)
	@pandoc --from=markdown --to=rst -o $@ $<


clean-docs:	## Remove built docs
	@rm -rf build/sphinx


preview-docs: docs	## Build and hosts docs locally
	@$(PYTHON) -B -m http.server -d build/sphinx \
	  -b 127.0.0.1 $(PORT)


##@ Workflow Features

project:	## project name
	@echo $(PROJECT)

version:	## project version
	@echo $(VERSION)

python:		## detected python executable
	@echo $(PYTHON)

release-notes:	## markdown variation of current version release notes
	@$(call checkfor,pandoc)
	@pandoc --from=rst --to=markdown -o - \
		docs/release_notes/v$(VERSION).rst


requires-git:
	@$(call checkfor,git)

requires-tox:
	@$(call checkfor,$(TOX))


.PHONY: archive build clean clean-built clean-docs default deploy-docs docs flake8 help mypy overview packaging-build packaging-test project python quick-test release-notes report-python requires-git requires-tox rpm srpm stage-docs test tidy version


# The end.
