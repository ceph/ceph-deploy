#!/usr/bin/env python
import os
import platform
import sys
"""
ceph-deploy - admin tool for ceph
"""

if os.path.exists('/usr/share/pyshared/ceph_deploy'):
    sys.path.insert(0,'/usr/share/pyshared/ceph_deploy')
elif os.path.exists('/usr/share/ceph-deploy'):
    sys.path.insert(0,'/usr/share/ceph-deploy')
elif os.path.exists('/usr/share/pyshared/ceph-deploy'):
    sys.path.insert(0,'/usr/share/pyshared/ceph-deploy')
elif os.path.exists('/usr/lib/python2.6/site-packages/ceph_deploy'):
    sys.path.insert(0,'/usr/lib/python2.6/site-packages/ceph_deploy')

from ceph_deploy.cli import main

if __name__ == '__main__':
    sys.exit(main())
