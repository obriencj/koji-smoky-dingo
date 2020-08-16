

PROJECT = kojismokydingo
VERSION = 0.9.0
ARCHIVE = $(PROJECT)-$(VERSION).tar.gz


default: test


clean:
	rm -rf *.egg-info dist/* build/*
	rm -f $(ARCHIVE)
	find -H . \
		\( -iname .tox -prune \) -o \
		\( -type d -iname __pycache__ -exec rm -rf {} + \)


packaging-test: clean archive
	rm -rf logs/*.log
	./tests/container/launch.sh


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
