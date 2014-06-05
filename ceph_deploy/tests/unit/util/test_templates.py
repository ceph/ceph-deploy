from textwrap import dedent
from ceph_deploy.util import templates


class TestCustomRepo(object):

    def test_only_repo_name(self):
        result = templates.custom_repo(reponame='foo')
        assert result == '[foo]'

    def test_second_line_with_good_value(self):
        result = templates.custom_repo(reponame='foo', enabled=0)
        assert result == '[foo]\nenabled=0'

    def test_mixed_values(self):
        result = templates.custom_repo(
            reponame='foo',
            enabled=0,
            gpgcheck=1,
            baseurl='example.org')
        assert result == dedent("""\
                        [foo]
                        baseurl=example.org
                        enabled=0
                        gpgcheck=1""")

    def test_allow_invalid_options(self):
        result = templates.custom_repo(reponame='foo', bar='bar')
        assert result == '[foo]'
