# Containerized Build Tooling

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

It should be safe to run `podman system prune` every now and then to
clean up orphaned layers, as the latest image builds will be safely
tagged, eg. ksd-test:rockylinux6 or ksd-test:fedora32


## Building Individual Containers

Running `./tools/launch-build.sh` will build and tag each
Containerfile in the ./tools directory. These files are named with a
suffix that indicates their platform, eg. Containerfile.rockylinux6 is
for building on Rocky Linux 6.

You can launch builds for individual platforms by name by specifiying
the platform as an argument to the launch-build.sh script.

`./tools/launch-build.sh rockylinux8` will cause only the
Containerfile.rockylinux8 to be used, producing an image tagged
ksd-test:rockylinux8

Any invocation of launch-build.sh is reliant on the archive having
been created first. This can be done by committing your work and
running `make archive` in the top project directory.

A final side-effect of running launch-build.sh is the copying of the
SRPM and RPMs to the dist directory.


## Older Platforms

The list of active platforms is stored in two places. The
`ACTIVE_PLATFORMS` variable in [common.sh] defines the selection of
platforms used by default if no specific platform list is specified.
There is a also platform matrix definition in [build_rpms.yml]

[common.sh]: ./common.sh
[build_rpms.yml]: ../.github/workflows/build_rpms.yml

I have in the past been removing older platforms as they fell off of
my radar. With the addition of these two lists as methods to manage
the defaults I will likely no longer delete Containerfiles as they
fall into EOL.
