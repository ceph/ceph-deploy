from mock import patch
from ceph_deploy.hosts import remotes


class FakeExists(object):

    def __init__(self, existing_paths):
        self.existing_paths = existing_paths

    def __call__(self, path):
        for existing_path in self.existing_paths:
            if path == existing_path:
                return path


class TestWhich(object):

    def setup(self):
        self.exists_module = 'ceph_deploy.hosts.remotes.os.path.exists'

    def test_finds_absolute_paths(self):
        exists = FakeExists(['/bin/ls'])
        with patch(self.exists_module, exists):
            path = remotes.which('ls')
        assert path == '/bin/ls'

    def test_does_not_find_executable(self):
        exists = FakeExists(['/bin/foo'])
        with patch(self.exists_module, exists):
            path = remotes.which('ls')
        assert path is None

