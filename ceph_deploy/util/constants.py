from os.path import join

# Base Path for ceph
base_path = '/var/lib/ceph'

# Base run Path
base_run_path = '/var/run/ceph'

tmp_path = join(base_path, 'tmp')

mon_path = join(base_path, 'mon')

mds_path = join(base_path, 'mds')

osd_path = join(base_path, 'osd')
