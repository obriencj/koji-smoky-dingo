# Sorry that this Makefile is a bit of a disaster.


PROJECT := kojismokydingo
VERSION := $(shell tools/version.sh)
ARCHIVE := $(PROJECT)-$(VERSION).tar.gz


PYTHON ?= $(shell which python3 python2 python 2>/dev/null \
	        | head -n1)
PYTHON := $(PYTHON)

_WHEELCHECK := $(shell $(PYTHON) -c 'import wheel' 2>/dev/null)
ifeq ($(.SHELLSTATUS),0)
	BDIST := bdist_wheel
	BDIST_FILE := dist/$(PROJECT)-$(VERSION)*.whl
else
	BDIST := build
	BDIST_FILE := .
endif

_FLAKE8CHECK := $(shell $(PYTHON) -c 'import flake8' 2>/dev/null)
ifeq ($(.SHELLSTATUS),0)
	FLAKE8 := flake8
else
	FLAKE8 :=
endif

# python 2.6 needed an externally installed argparse, which has weird
# output for some things (like mutually exclusive groups), so we skip
# that test for 2.6
_OLDCHECK := $(shell $(PYTHON) -c 'import sys; sys.exit(sys.version_info < (2, 7,))')
ifeq ($(.SHELLSTATUS),0)
	NOSEARGS :=
else
	NOSEARGS := -e 'test_command_help'
endif


# what I really want is for the $(ARCHIVE) target to be able to
# compare the timestamp of that file vs. the timestamp of the last
# commit in the repo.
GITHEAD := $(shell cut -f2 -d' ' .git/HEAD)
GITHEADREF := .git/$(GITHEAD)

# We use this later in setting up the gh-pages submodule for pushing,
# so forks will push their docs to their own gh-pages branch.
ORIGIN_PUSH = $(shell git remote get-url --push origin)


##@ Basic Targets
default: quick-test	## Runs the quick-test target


help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)


##@ Local Build and Install
build: clean	## Produces a wheel using the default system python
	@$(PYTHON) setup.py $(FLAKE8) $(BDIST)


install: build	## Installs using the default python for the current user
	@$(PYTHON) -B -m pip.__main__ \
		install --no-deps --user -I $(BDIST_FILE)


##@ Cleanup
tidy:	## Removes stray eggs and .pyc files
	@rm -rf *.egg-info
	@find -H . \
		\( -iname '.tox' -o -iname '.eggs' -prune \) -o \
		\( -type d -iname '__pycache__' -exec rm -rf {} + \) -o \
		\( -type f -iname '*.pyc' -exec rm -f {} + \)


clean: tidy	## Removes built content, test logs, coverage reports
	@rm -rf .coverage* build/* dist/* htmlcov/* logs/*
	@if [ -f "$(ARCHIVE)" ] ; then rm -f "$(ARCHIVE)" ; fi


##@ Containerized RPMs
packaging-build: $(ARCHIVE)	## Launches all containerized builds
	@./tools/launch-build.sh


packaging-test: packaging-build	## Launches all containerized tests
	@rm -rf logs/*
	@./tools/launch-test.sh


##@ Testing
test: clean	## Launches tox
	@tox


quick-test: build	## Launches nosetest using the default python
	@$(PYTHON) -B setup.py test $(NOSEARGS)


##@ RPMs
srpm: $(ARCHIVE)	## Produce an SRPM from the archive
	@rpmbuild \
		--define "_srcrpmdir dist" \
		--define "dist %{nil}" \
		-ts "$(ARCHIVE)"


rpm: $(ARCHIVE)		## Produce an RPM from the archive
	@rpmbuild --define "_rpmdir dist" -tb "$(ARCHIVE)"


archive: $(ARCHIVE)	## Extracts an archive from the current git commit


# newer versions support the --format tar.gz but we're intending to work all
# the way back to RHEL 6 which does not have that.
$(ARCHIVE): $(GITHEADREF)
	@git archive $(GITHEAD) \
		--format tar --prefix "$(PROJECT)-$(VERSION)/" \
		| gzip > "$(ARCHIVE)"


##@ Documentation
docs: docs/overview.rst	## Build sphinx docs
	@$(PYTHON) -B setup.py docs


overview: docs/overview.rst  ## rebuilds the overview from README.md


docs/overview.rst: README.md
	@sed 's/^\[\!.*/ /g' $< > overview.md
	@pandoc --from=markdown --to=rst -o $@ "overview.md"
	@rm -f overview.md


pull-docs:	## Refreshes the gh-pages submodule
	@git submodule init ; \
	pushd gh-pages >/dev/null ; \
	git reset --hard origin/gh-pages ; \
	git pull ; \
	git clean -fd >/dev/null ; \
	popd >/dev/null


stage-docs: docs pull-docs	## Builds docs and stages them in gh-pages
	@pushd gh-pages >/dev/null ; \
	rm -rf * ; \
	touch .nojekyll ; \
	popd >/dev/null ; \
	cp -vr build/sphinx/dirhtml/* gh-pages/


deploy-docs: stage-docs	## Builds, stages, and deploys docs to gh-pages
	@pushd gh-pages >/dev/null ; \
	git remote set-url --push origin $(ORIGIN_PUSH) ; \
	git add -A && git commit -m "deploying sphinx update" && git push ; \
	popd >/dev/null ; \
	if [ `git diff --name-only gh-pages` ] ; then \
		git add gh-pages ; \
		git commit -m "docs deploy [ci skip]" -o gh-pages ; \
	fi


clean-docs:	## Remove built docs
	@rm -rf build/sphinx/*


.PHONY: archive build clean clean-docs default deploy-docs docs help overview packaging-build packaging-test quick-test rpm srpm stage-docs test tidy


# The end.
