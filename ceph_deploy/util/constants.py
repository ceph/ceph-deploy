from os.path import join

# Base Path for ceph
base_path = '/var/lib/ceph'

tmp_path = join(base_path, 'tmp')

mon_path = join(base_path, 'mon')

mds_path = join(base_path, 'mds')
