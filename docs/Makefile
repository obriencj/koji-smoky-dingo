# Makefile for Sphinx documentation
#

SHELL = /bin/bash

# You can set these variables from the command line.
SPHINXOPTS    =
_SPHINXBUILD   = sphinx-build
SPHINXBUILD   = python3 -B -m sphinx.__main__
PAPER         =
BUILDDIR      = _build

PYTHONPATH := `echo ../build/lib*`
SPHINXCMD := PYTHONPATH=${PYTHONPATH} $(SPHINXBUILD)

DEPLOYDIR = _deploy
DEPLOYFORMAT = dirhtml
DEPLOYREPO = git@github.com:/obriencj/koji-smoky-dingo
DEPLOYBRANCH = gh-pages


# User-friendly check for sphinx-build
ifeq ($(shell which $(_SPHINXBUILD) >/dev/null 2>&1; echo $$?), 1)
$(error The '$(_SPHINXBUILD)' command was not found.)
endif


# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

# the i18n builder cannot share the environment and doctrees with the others
I18NSPHINXOPTS  = $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .


.PHONY: help clean html dirhtml pickle json changes linkcheck deploy

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  deploy     to run $(DEPLOYFORMAT) and push to the $(DEPLOYBRANCH) branch under $(DEPLOYDIR)"
	@echo "  html       to make standalone HTML files"
	@echo "  dirhtml    to make HTML files named index.html in directories"
	@echo "  pickle     to make pickle files"
	@echo "  json       to make JSON files"
	@echo "  changes    to make an overview of all changed/added/deprecated items"
	@echo "  linkcheck  to check all external links for integrity"

clean:
	rm -rf $(BUILDDIR)/*

html: generate
	$(SPHINXCMD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

dirhtml: generate
	@${SPHINXCMD} -b dirhtml $(ALLSPHINXOPTS) $(BUILDDIR)/dirhtml
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/dirhtml."

singlehtml: generate
	$(SPHINXCMD) -b singlehtml $(ALLSPHINXOPTS) $(BUILDDIR)/singlehtml
	@echo
	@echo "Build finished. The HTML page is in $(BUILDDIR)/singlehtml."

pickle: generate
	$(SPHINXCMD) -b pickle $(ALLSPHINXOPTS) $(BUILDDIR)/pickle
	@echo
	@echo "Build finished; now you can process the pickle files."

json: generate
	$(SPHINXCMD) -b json $(ALLSPHINXOPTS) $(BUILDDIR)/json
	@echo
	@echo "Build finished; now you can process the JSON files."

changes: generate
	$(SPHINXCMD) -b changes $(ALLSPHINXOPTS) $(BUILDDIR)/changes
	@echo
	@echo "The overview file is in $(BUILDDIR)/changes."

linkcheck: generate
	$(SPHINXCMD) -b linkcheck $(ALLSPHINXOPTS) $(BUILDDIR)/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in $(BUILDDIR)/linkcheck/output.txt."

dirs: _static _templates $(DEPLOYDIR)

_static _templates $(DEPLOYDIR):
	mkdir -p $@

build-project:
	pushd ../ >/dev/null ;\
	./setup.py clean build ;\
	popd

overview.rst: ../README.md
	sed 's/^\[\!.*/ /g' ../README.md > overview.md
	pandoc --from=markdown --to=rst -o "overview.rst" "overview.md"
	rm -f overview.md

generate: build-project overview.rst

# clones the appropriate git repo and branch in the deploy directory
# if it isn't already setup
setup-stage: $(DEPLOYDIR)
	if ! [ -d "$(DEPLOYDIR)/.git" ] ; then \
		git clone $(DEPLOYREPO) $(DEPLOYDIR) \
			--single-branch \
			--branch $(DEPLOYBRANCH) ;\
	fi ;\

# clears out the old contents of _deploy so that we can replace them
# with our newly generated version
clean-stage: setup-stage
	pushd $(DEPLOYDIR) ;\
	git checkout --force $(DEPLOYBRANCH) ;\
	git pull ;\
	git rm -rf * ;\
	rm -rf * ;\
	touch .nojekyll ; git add .nojekyll ;\
	popd

stage: generate clean-stage $(DEPLOYFORMAT)
	cp -r "$(BUILDDIR)/$(DEPLOYFORMAT)/"* $(DEPLOYDIR)
	pushd $(DEPLOYDIR) ;\
	git add . ;\
	popd

# builds the selected format of docs, and checks them into the right
# branch on our repo.
deploy: stage
	pushd $(DEPLOYDIR) ;\
	git commit -m "deploying sphinx update" ;\
	git push ;\
	popd


# The end.
