# Sorry that this Makefile is a bit of a disaster.


PROJECT = kojismokydingo
VERSION = $(shell tools/version.sh)
ARCHIVE = $(PROJECT)-$(VERSION).tar.gz


default: test


clean: clean-docs
	rm -rf *.egg-info dist/* build/* logs/*
	rm -f "$(ARCHIVE)"
	find -H . \
		\( -iname '.tox' -prune \) -o \
		\( -type d -iname '__pycache__' -exec rm -rf {} + \) -o \
		\( -type f -iname '*.pyc' -exec rm -f {} + \)


packaging-build: archive
	./tools/launch-build.sh


packaging-test: packaging-build
	rm -rf logs/*
	./tools/launch-test.sh


test: clean
	tox


srpm: $(ARCHIVE)
	rpmbuild --define "_srcrpmdir dist" -ts "$(ARCHIVE)"


rpm: $(ARCHIVE)
	rpmbuild --define "_rpmdir dist" -tb "$(ARCHIVE)"


archive: $(ARCHIVE)


# newer versions support the --format tar.gz but we're intending to work all
# the way back to RHEL 6 which does not have that.
$(ARCHIVE):
	git archive HEAD \
		--format tar --prefix "$(PROJECT)-$(VERSION)/" \
		| gzip > "$(ARCHIVE)"


docs:
	make -C docs html


deploy-docs:
	make -C docs deploy


clean-docs:
	make -C docs clean


.PHONY: all archive clean default docs deploy-docs packaging-build packaging-test rpm srpm test


# The end.
