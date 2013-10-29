from setuptools import setup, find_packages
import os
import sys
import ceph_deploy
from vendor import vendorize


def read(fname):
    path = os.path.join(os.path.dirname(__file__), fname)
    f = open(path)
    return f.read()

install_requires = []
pyversion = sys.version_info[:2]
if pyversion < (2, 7) or (3, 0) <= pyversion <= (3, 1):
    install_requires.append('argparse')

#
# Add libraries that are not part of install_requires
#
vendorize([
    ('remoto', '0.0.11'),
])


setup(
    name='ceph-deploy',
    version=ceph_deploy.__version__,
    packages=find_packages(),

    author='Inktank',
    author_email='ceph-devel@vger.kernel.org',
    description='Deploy Ceph with minimal infrastructure',
    long_description=read('README.rst'),
    license='MIT',
    keywords='ceph deploy',
    url="https://github.com/ceph/ceph-deploy",

    install_requires=[
        'setuptools',
        ] + install_requires,

    tests_require=[
        'pytest >=2.1.3',
        'mock >=1.0b1',
        ],

    entry_points={

        'console_scripts': [
            'ceph-deploy = ceph_deploy.cli:main',
            ],

        'ceph_deploy.cli': [
            'new = ceph_deploy.new:make',
            'install = ceph_deploy.install:make',
            'uninstall = ceph_deploy.install:make_uninstall',
            'purge = ceph_deploy.install:make_purge',
            'purgedata = ceph_deploy.install:make_purge_data',
            'mon = ceph_deploy.mon:make',
            'gatherkeys = ceph_deploy.gatherkeys:make',
            'osd = ceph_deploy.osd:make',
            'disk = ceph_deploy.osd:make_disk',
            'mds = ceph_deploy.mds:make',
            'forgetkeys = ceph_deploy.forgetkeys:make',
            'config = ceph_deploy.config:make',
            'admin = ceph_deploy.admin:make',
            ],

        },
    )
