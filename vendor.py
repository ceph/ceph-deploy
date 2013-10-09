import subprocess
import os
from os import path
import traceback


error_msg = """
This library depends on sources fetched when packaging that failed to be
retrieved.

This means that it will *not* work as expected. Errors encountered:
"""


def run(cmd):
    print '[vendoring] Running command: %s' % ' '.join(cmd)
    try:
        result = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
    except Exception as error:
        print_error([], traceback.format_exc(error).split('\n'))
        raise SystemExit(1)

    if result.wait():
        print_error(result.stdout.readlines(), result.stderr.readlines())


def print_error(stdout, stderr):
    print '*'*80
    print error_msg
    for line in stdout:
        print line
    for line in stderr:
        print line
    print '*'*80


def vendor_library(name, version):
    this_dir = path.dirname(path.abspath(__file__))
    vendor_dest = path.join(this_dir, 'ceph_deploy/lib/%s' % name)
    vendor_src = path.join(this_dir, name)
    vendor_module = path.join(vendor_src, name)
    current_dir = os.getcwd()

    if path.exists(vendor_src):
        run(['rm', '-rf', vendor_src])

    if path.exists(vendor_dest):
        module = __import__('ceph_deploy.lib.remoto', globals(), locals(), ['__version__'])
        if module.__version__ != version:
            run(['rm', '-rf', vendor_dest])

    if not path.exists(vendor_dest):
        run(['git', 'clone', 'git://ceph.com/%s' % name])
        os.chdir(vendor_src)
        run(['git', 'checkout', version])
        run(['mv', vendor_module, vendor_dest])
    os.chdir(current_dir)


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
        name, version = library
        vendor_library(name, version)
