# Sorry that this Makefile is a bit of a disaster.


PROJECT = kojismokydingo
VERSION = $(shell tools/version.sh)
ARCHIVE = $(PROJECT)-$(VERSION).tar.gz

GITBRANCH = $(shell git branch --show-current)
GITHEADREF = $(shell git show-ref -d --heads $(GITBRANCH) \
		| head -n1 | cut -f2 -d' ')

PYTHON ?= $(shell which python3 python2 python 2>/dev/null \
	        | head -n1)


# We use this later in setting up the gh-pages submodule for pushing,
# so forks will push their docs to their own gh-pages branch.
ORIGIN_PUSH = $(shell git remote get-url --push origin)

##@ Valid Targets
help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)


default: quick-test	## Runs the quick-test target


build: clean	## Produces a wheel using the default system python
	@$(PYTHON) setup.py flake8 bdist_wheel


install: build	## Installs using the default python for the current user
	@$(PYTHON) -B -m pip install --no-deps --user -I dist/*.whl


tidy:	## Removes stray eggs and .pyc files
	@rm -rf *.egg-info
	@find -H . \
		\( -iname '.tox' -o -iname '.eggs' -prune \) -o \
		\( -type d -iname '__pycache__' -exec rm -rf {} + \) -o \
		\( -type f -iname '*.pyc' -exec rm -f {} + \)


clean: tidy	## Removes built content, test logs, coverage reports
	@rm -rf .coverage* build/* dist/* htmlcov/* logs/*
	@rm -f "$(ARCHIVE)"


packaging-build: $(ARCHIVE)	## Launches all containerized builds
	@./tools/launch-build.sh


packaging-test: packaging-build	## Launches all containerized tests
	@rm -rf logs/*
	@./tools/launch-test.sh


test: clean	## Launches tox
	@tox


quick-test: clean	## Launches nosetest using the default python
	@$(PYTHON) -B setup.py flake8 build test


srpm: $(ARCHIVE)	## Produce an SRPM from the current git commit
	@rpmbuild \
		--define "_srcrpmdir dist" \
		--define "dist %{nil}" \
		-ts "$(ARCHIVE)"


rpm: $(ARCHIVE)		## Produce an RPM from the current git commit
	@rpmbuild --define "_rpmdir dist" -tb "$(ARCHIVE)"


archive: $(ARCHIVE)	## Extracts an archive from the current git commit


# newer versions support the --format tar.gz but we're intending to work all
# the way back to RHEL 6 which does not have that.
$(ARCHIVE): .git/$(GITHEADREF)
	@git archive $(GITHEADREF) \
		--format tar --prefix "$(PROJECT)-$(VERSION)/" \
		| gzip > "$(ARCHIVE)"


docs/overview.rst: README.md
	@sed 's/^\[\!.*/ /g' $< > overview.md
	@pandoc --from=markdown --to=rst -o $@ "overview.md"
	@rm -f overview.md


docs: docs/overview.rst	## Build sphinx docs
	@$(PYTHON) -B setup.py docs


pull-docs:	## Refreshes the gh-pages submodule
	@git submodule init ; \
	pushd gh-pages ; \
	git reset --hard gh-pages ; \
	git pull ; \
	popd


stage-docs: docs pull-docs	## Builds docs and stages them in gh-pages
	@pushd gh-pages ; \
	git reset --hard origin/gh-pages ; \
	git pull ; \
	rm -rf * ; \
	touch .nojekyll ; \
	popd ; \
	cp -r build/sphinx/dirhtml/* gh-pages


deploy-docs: stage-docs	## Build, stage, and deploy docs to gh-pages
	@pushd gh-pages ; \
	git remote set-url --push origin $(ORIGIN_PUSH) ; \
	git commit -a -m "deploying sphinx update" && git push ; \
	popd ; \
	if [ `git diff --name-only gh-pages` ] ; then \
		git add gh-pages ; \
		git commit -m "docs deploy" -o gh-pages ; \
	fi


clean-docs:	## Remove built docs
	@rm -rf build/sphinx/*


.PHONY: all archive clean default docs deploy-docs help overview packaging-build packaging-test rpm srpm stage-docs test


# The end.
