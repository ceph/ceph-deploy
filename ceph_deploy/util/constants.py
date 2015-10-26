from os.path import join
from collections import namedtuple

# Base Path for ceph
base_path = '/var/lib/ceph'

# Base run Path
base_run_path = '/var/run/ceph'

tmp_path = join(base_path, 'tmp')

mon_path = join(base_path, 'mon')

mds_path = join(base_path, 'mds')

osd_path = join(base_path, 'osd')

# Default package components to install
_base_components = [
    'ceph-osd',
    'ceph-mds',
    'ceph-mon',
]

default_components = namedtuple('DefaultComponents', ['rpm', 'deb'])

# the difference here is because RPMs currently name the radosgw differently than DEBs.
# TODO: This needs to get unified once the packaging naming gets consistent
default_components.rpm = tuple(_base_components + ['ceph-radosgw'])
default_components.deb = tuple(_base_components + ['radosgw'])

gpg_key_base_url = "download.ceph.com/keys/"
