
Some scripts for building RPMs across a diverse range of platforms.

These are intended to be invoked from the parent directory, or via the
make targets `packaging-build` and `packaging-test`

`make packaging-build` will invoke tools/launch-build.sh which will in
turn identify a platform (or all platforms) with a Containerfile in
this directory. It will then build the appropriate image(s), which
will in turn cause the image to resolve and install dependencies and
then build the SRPM and RPMs for that platform. Results will be in the
dist directory

`make packaging-test` depends on the packaging-build target to first
ensure that the images are built and available. After that, a
container is launched for the relevant platform(s), and a series of
tests are invoked in that environment. The output of the tests is
written to the logs directory

This tooling is intended to function with either podman or docker, in
that order of preference. It tried to make good use of layer caching
to speed up the process, so only the final layer which produces and
installs the RPM should normally be run (and then only if the tarball
has been regenerated). Old images are discarded when new images are
introduced.