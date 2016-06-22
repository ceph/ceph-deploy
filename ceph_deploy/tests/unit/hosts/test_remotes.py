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
