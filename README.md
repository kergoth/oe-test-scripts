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

    ./greedy-deps-tests -p libusb1 -s -w libpcap

Example output of this command:

    $ ./greedy-deps-tests -p libusb1 -s -w libpcap
    Wiping temp directory...done
    Wiping buildhistory directory...done
    Building libpcap from scratch...done
    Building libusb1 to prepopulate tmpdir...done
    Cleaning libpcap...done
    Rebuilding libpcap...done
    Checking buildhistory for libpcap...failed
    Differences in buildhistory for libpcap:
    packages/i586-mel-linux/libpcap/libpcap-dbg: RRECOMMENDS: added "libusb1-dbg"
    packages/i586-mel-linux/libpcap/libpcap-dev: RRECOMMENDS: added "libusb1-dev"
    packages/i586-mel-linux/libpcap/libpcap: RDEPENDS: added "libusb1 (['>= 1.0.9'])"

leaky-layer-tests
-----------------

This is a simple script which uses a default configuration (poky/qemux86), and
adds each available bsp or distro layer to the configuration, one at a time,
monitoring for changes to the appended recipes with bitbake-whatchanged. This
helps one to identify bsp layers which affect machines other than the ones it
provides, and distro layers which affect other distros when included.
