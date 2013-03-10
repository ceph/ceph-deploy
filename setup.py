#!/usr/bin/python
from setuptools import setup, find_packages
import os
import sys


def read(fname):
    path = os.path.join(os.path.dirname(__file__), fname)
    f = open(path)
    return f.read()

install_requires = []
pyversion = sys.version_info[:2]
if pyversion < (2, 7) or (3, 0) <= pyversion <= (3, 1):
    install_requires.append('argparse')

setup(
    name='ceph-deploy',
    version='0.0.1',
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
            'discover = ceph_deploy.discover:make',
            'install = ceph_deploy.install:make',
            'uninstall = ceph_deploy.install:make_uninstall',
            'purge = ceph_deploy.install:make_purge',
            'mon = ceph_deploy.mon:make',
            'gatherkeys = ceph_deploy.gatherkeys:make',
            'osd = ceph_deploy.osd:make',
            'mds = ceph_deploy.mds:make',
            'forgetkeys = ceph_deploy.forgetkeys:make',
            'config = ceph_deploy.config:make',
            'admin = ceph_deploy.admin:make',
            'zapdisk = ceph_deploy.zapdisk:make',
            ],

        },
    )
