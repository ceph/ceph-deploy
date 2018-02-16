try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

from ceph_deploy.hosts import remotes


class TestObjectGrep(object):

    def setup(self):
        self.file_object = StringIO('foo\n')
        self.file_object.seek(0)

    def test_finds_term(self):
        assert remotes.object_grep('foo', self.file_object)

    def test_does_not_find_anything(self):
        assert remotes.object_grep('bar', self.file_object) is False


class TestWhich(object):

    def test_executable_is_a_directory(self, monkeypatch):
        monkeypatch.setattr(remotes.os.path, 'exists', lambda x: True)
        monkeypatch.setattr(remotes.os.path, 'isfile', lambda x: False)
        assert remotes.which('foo') is None

    def test_executable_does_not_exist(self, monkeypatch):
        monkeypatch.setattr(remotes.os.path, 'exists', lambda x: False)
        monkeypatch.setattr(remotes.os.path, 'isfile', lambda x: True)
        assert remotes.which('foo') is None

    def test_executable_exists_as_file(self, monkeypatch):
        monkeypatch.setattr(remotes.os.path, 'exists', lambda x: True)
        monkeypatch.setattr(remotes.os.path, 'isfile', lambda x: True)
        assert remotes.which('foo') == '/usr/local/bin/foo'
