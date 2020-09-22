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


default: build


build: clean
	@$(PYTHON) setup.py clean flake8 bdist_wheel


install: build
	@$(PYTHON) -B -m pip install --no-deps --user -I dist/*.whl


tidy:
	@rm -rf *.egg-info
	@find -H . \
		\( -iname '.tox' -o -iname '.eggs' -prune \) -o \
		\( -type d -iname '__pycache__' -exec rm -rf {} + \) -o \
		\( -type f -iname '*.pyc' -exec rm -f {} + \)


clean: tidy
	@rm -rf .coverage* build/* dist/* htmlcov/* logs/*
	@rm -f "$(ARCHIVE)"


packaging-build: $(ARCHIVE)
	@./tools/launch-build.sh


packaging-test: packaging-build
	@rm -rf logs/*
	@./tools/launch-test.sh


test: clean
	@tox


srpm: $(ARCHIVE)
	@rpmbuild \
		--define "_srcrpmdir dist" \
		--define "dist %{nil}" \
		-ts "$(ARCHIVE)"


rpm: $(ARCHIVE)
	@rpmbuild --define "_rpmdir dist" -tb "$(ARCHIVE)"


archive: $(ARCHIVE)


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


docs: docs/overview.rst
	@$(PYTHON) -B setup.py docs


pull-docs:
	@git submodule init ; \
	pushd gh-pages ; \
	git reset --hard gh-pages ; \
	git pull ; \
	popd


stage-docs: docs pull-docs
	@pushd gh-pages ; \
	git reset --hard origin/gh-pages ; \
	git pull ; \
	rm -rf * ; \
	touch .nojekyll ; \
	popd ; \
	cp -r build/sphinx/dirhtml/* gh-pages


deploy-docs: stage-docs
	@pushd gh-pages ; \
	git remote set-url --push origin $(ORIGIN_PUSH) ; \
	git commit -a -m "deploying sphinx update" && git push ; \
	popd ; \
	if [ `git diff --name-only gh-pages` ] ; then \
		git add gh-pages ; \
		git commit -m "docs deploy" -o gh-pages ; \
	fi


clean-docs:
	@rm -rf build/sphinx/*


.PHONY: all archive clean default docs deploy-docs overview packaging-build packaging-test rpm srpm stage-docs test


# The end.
