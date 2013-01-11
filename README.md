oe-test-scripts
===============

Some testing scripts I use for OE/bitbake/yocto

These expect to be run from a functional bitbake build environment.

reloc-tests
-----------

This script tests for relocation errors in tools we run during the build

It does so by building the specified target, then rebuilding all of its
dependencies from scratch in a new tmpdir, with all their dependencies
pulled from sstates produced in the previous tmpdir.

This has been verified functional by removing flex-native's `create_wrapper`
call, then building something which depends upon flex/bison.

greedy-deps-tests
-----------------

This script tests for greedy configure scripts in recipe builds, which link
against things based on their existence in the sysroot.

It does so by building the specified target, then rebuilding all of its
dependencies from scratch, one by one, monitoring for buildhistory changes.

This has been verified functional by spotting libpcap's tendency to pull in
libusb functionality if libusb is available. To reproduce this:

    ./greedy-deps-tests -p libusb1 -s libpcap
