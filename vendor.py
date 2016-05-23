from __future__ import print_function

import subprocess
import os
from os import path
import re
import traceback
import sys


error_msg = """
This library depends on sources fetched when packaging that failed to be
retrieved.

This means that it will *not* work as expected. Errors encountered:
"""


def run(cmd):
    print('[vendoring] Running command: %s' % ' '.join(cmd))
    try:
        result = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
    except Exception:
        # if building with python2.5 this makes it compatible
        _, error, _ = sys.exc_info()
        print_error([], traceback.format_exc(error).split('\n'))
        raise SystemExit(1)

    if result.wait():
        print_error(result.stdout.readlines(), result.stderr.readlines())

    return result.returncode


def print_error(stdout, stderr):
    print('*'*80)
    print(error_msg)
    for line in stdout:
        print(line)
    for line in stderr:
        print(line)
    print('*'*80)


def vendor_library(name, version, cmd=None):
    this_dir = path.dirname(path.abspath(__file__))
    vendor_dest = path.join(this_dir, 'ceph_deploy/lib/vendor/%s' % name)
    vendor_init = path.join(vendor_dest, '__init__.py')
    vendor_src = path.join(this_dir, name)
    vendor_module = path.join(vendor_src, name)
    current_dir = os.getcwd()

    if path.exists(vendor_src):
        run(['rm', '-rf', vendor_src])

    if path.exists(vendor_init):
        # The following read/regex is done so that we can parse module metadata without the need
        # to import it. Module metadata is defined as variables with double underscores. We are
        # particularly insteresting in the version string, so we look into single or double quoted
        # values, like:  __version__ = '1.0'
        module_file = open(vendor_init).read()
        metadata = dict(re.findall(r"__([a-z]+)__\s*=\s*['\"]([^'\"]*)['\"]", module_file))
        if metadata.get('version') != version:
            run(['rm', '-rf', vendor_dest])

    if not path.exists(vendor_dest):
        rc = run(['git', 'clone', 'git://git.ceph.com/%s' % name])
        if rc:
            print("%s: git clone failed using ceph.com url with rc %s, trying github.com" % (path.basename(__file__), rc))
            run(['git', 'clone', 'https://github.com/ceph/%s.git' % name])
        os.chdir(vendor_src)
        run(['git', 'checkout', version])
        if cmd:
            run(cmd)
        run(['mv', vendor_module, vendor_dest])
    os.chdir(current_dir)


def clean_vendor(name):
    """
    Ensure that vendored code/dirs are removed, possibly when packaging when
    the environment flag is set to avoid vendoring.
    """
    this_dir = path.dirname(path.abspath(__file__))
    vendor_dest = path.join(this_dir, 'ceph_deploy/lib/vendor/%s' % name)
    run(['rm', '-rf', vendor_dest])


def vendorize(vendor_requirements):
    """
    This is the main entry point for vendorizing requirements. It expects
    a list of tuples that should contain the name of the library and the
    version.

    For example, a library ``foo`` with version ``0.0.1`` would look like::

        vendor_requirements = [
            ('foo', '0.0.1'),
        ]
    """

    for library in vendor_requirements:
        if len(library) == 2:
            name, version = library
            cmd = None
        elif len(library) == 3:  # a possible cmd we need to run
            name, version, cmd = library
        vendor_library(name, version, cmd)
