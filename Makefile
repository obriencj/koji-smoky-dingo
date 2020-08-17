

PROJECT = kojismokydingo
VERSION = $(shell tools/version.sh)
ARCHIVE = $(PROJECT)-$(VERSION).tar.gz


default: test


clean:
	rm -rf *.egg-info dist/* build/* logs/*
	rm -f $(ARCHIVE)
	find -H . \
		\( -iname .tox -prune \) -o \
		\( -type d -iname __pycache__ -exec rm -rf {} + \) -o \
		\( -type f -iname *.pyc -exec rm -f {} + \)


packaging-build: archive
	./tools/launch-build.sh


packaging-test: packaging-build
	rm -rf logs/*
	./tools/launch-test.sh


test: clean
	tox


srpm: $(ARCHIVE)
	rpmbuild -ts $(ARCHIVE)


rpm: $(ARCHIVE)
	rpmbuild -tb $(ARCHIVE)


archive: $(ARCHIVE)


$(ARCHIVE):
	git archive HEAD \
		--format tar --prefix $(PROJECT)-$(VERSION)/ \
		| gzip > $(ARCHIVE)


.PHONY: all archive clean default packaging-test rpm srpm test


# The end.
