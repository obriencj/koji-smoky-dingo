# Overview of Sifty Sieves Examples

This is a collection of simple examples demonstrating how to use standalone
sifty filters to work with collections of builds.


## comparison.sift

This is a simple check to see what builds are up-level or down-level compared
to those in another tag. It uses the ksd-filter-builds standalone to make
the filter behave like a script.

```
#! /usr/bin/env ksd-filter-builds

;; declare that this filter needs a RELEASE_TAG parameter
#param RELEASE_TAG

;; unless otherwise set via the command-line --profile option, use the
;; "koji-internal" koji profile. This profile must be present in the
;; system or user koji configuration.
#option --profile=koji-internal

;; unless otherwise set via the command-line, the output option will
;; be used to write out one file for each flag, containing the NVRs
;; which have that flag set.
#option --output=*:%.txt

;; set the "obsoletes" flag on any filtered build which has an NVR
;; less-than or equal-to the latest build of the same package in the
;; given $RELEASE_TAG tag.
(flag obsoletes (compare-latest-nvr <= $RELEASE_TAG))

;; set the "upgrades" flag on any filtered build which has an NVR
;; greater-than the latest build of the same package in the given
;; $RELEASE_TAG tag.
(flag upgrades (compare-latest-nvr > $RELEASE_TAG))

;; The end.
```

Looking at the filter, we can see that there's a line declaring a
param named `RELEASE_TAG`, and this param is then used in two sieve
predicates.

We can also see two lines declaring defaults for the `--profile`
option and the `--output` option. These are used only if the options
are not specified directly on the command-line when the filter is
invoked.

To construct an example, let's pretend we have a tag named
"foo-bar-1-candidates" containing work-in-progress builds, and another
tag named "foo-bar-1.2-released" containing released work for the 1.2
version of the foo-bar project.


Thus, we can run:
```bash
./comparison.sift \
    --tag foo-bar-1-candidate \
    -P RELEASE_TAG=foo-bar-1.2-released
```

This indicates that the filter should run against all of the builds
tagged into our foo-bar-1-candidate tag. It also indicates that the value
of the RELEASE_TAG parameter is foo-bar-1.2-released.

Up to two files will be written in the current working directory based
on this invocation. A file named "obsoletes.txt" will be written
containing all of the NVRs from foo-bar-1-candidate which have an NVR
less-than or equal-to the latest build of the same package in
foo-bar-1.2-released.  A file named "upgrades.txt" will be written
containing all of the NVRs from foo-bar-1-candidate which have an NVR
greater-than the latest build of the same package in
foo-bar-1.2-released.
