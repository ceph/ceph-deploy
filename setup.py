#!/usr/bin/python
from setuptools import setup, find_packages
import os
import sys
import subprocess


def read(fname):
    path = os.path.join(os.path.dirname(__file__), fname)
    f = open(path)
    return f.read()

def get_version():
    try:
        ver = os.environ['CEPH_DEPLOY_VERSION_FOR_PYTHON']
        # spec might pass trailing '-'; handle it
        if ver[-1:] == '-':
            ver = ver[:-1]
    except:
        ver = subprocess.check_output(['/usr/bin/git', 'describe']).rstrip()
        if ver.startswith('v'):
            ver = ver[1:]
    return ver

install_requires = []
pyversion = sys.version_info[:2]
if pyversion < (2, 7) or (3, 0) <= pyversion <= (3, 1):
    install_requires.append('argparse')

setup(
    name='ceph-deploy',
    version=get_version(),
    packages=find_packages(),

    author='Tommi Virtanen',
    author_email='tommi.virtanen@inktank.com',
    description='Deploy Ceph with minimal infrastructure',
    long_description=read('README.rst'),
    license='MIT',
    keywords='ceph deploy',
    url="https://github.com/ceph/ceph-deploy",

    install_requires=[
        'setuptools',
        'pushy >=0.5.1',
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
