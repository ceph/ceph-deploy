from ceph_deploy.hosts import centos
from ceph_deploy import hosts
from mock import Mock, patch


def pytest_generate_tests(metafunc):
    # called once per each test function
    try:
        funcarglist = metafunc.cls.params[metafunc.function.__name__]
    except AttributeError:
        return
    argnames = list(funcarglist[0])
    metafunc.parametrize(argnames, [[funcargs[name] for name in argnames]
                                    for funcargs in funcarglist])


class TestCentosRepositoryUrlPart(object):

    params= {
        'test_repository_url_part': [
            dict(distro="CentOS Linux", release='4.3', codename="Foo", output='el6'),
            dict(distro="CentOS Linux", release='6.5', codename="Final", output='el6'),
            dict(distro="CentOS Linux", release='7.0', codename="Core", output='el7'),
            dict(distro="CentOS Linux", release='7.0.1406', codename="Core", output='el7'),
            dict(distro="CentOS Linux", release='10.4.000', codename="Core", output='el10'),
            dict(distro="RedHat", release='4.3', codename="Foo", output='el6'),
            dict(distro="Red Hat Enterprise Linux Server", release='5.8', codename="Tikanga", output="el6"),
            dict(distro="Red Hat Enterprise Linux Server", release='6.5', codename="Santiago", output='rhel6'),
            dict(distro="RedHat", release='7.0.1406', codename="Core", output='rhel7'),
            dict(distro="RedHat", release='10.999.12', codename="Core", output='rhel10'),
            ],
        'test_rpm_dist': [
            dict(distro="CentOS Linux", release='4.3', codename="Foo", output='el6'),
            dict(distro="CentOS Linux", release='6.5', codename="Final", output='el6'),
            dict(distro="CentOS Linux", release='7.0', codename="Core", output='el7'),
            dict(distro="CentOS Linux", release='7.0.1406', codename="Core", output='el7'),
            dict(distro="CentOS Linux", release='10.10.9191', codename="Core", output='el10'),
            dict(distro="RedHat", release='4.3', codename="Foo", output='el6'),
            dict(distro="Red Hat Enterprise Linux Server", release='5.8', codename="Tikanga", output="el6"),
            dict(distro="Red Hat Enterprise Linux Server", release='6.5', codename="Santiago", output='el6'),
            dict(distro="RedHat", release='7.0', codename="Core", output='el7'),
            dict(distro="RedHat", release='7.0.1406', codename="Core", output='el7'),
            dict(distro="RedHat", release='10.9.8765', codename="Core", output='el10'),
        ]
    }

    def make_fake_connection(self, platform_information=None):
        get_connection = Mock()
        get_connection.return_value = get_connection
        get_connection.remote_module.platform_information = Mock(
            return_value=platform_information)
        return get_connection

    def test_repository_url_part(self, distro, release, codename, output):
        fake_get_connection = self.make_fake_connection((distro, release, codename))
        with patch('ceph_deploy.hosts.get_connection', fake_get_connection):
            self.module = hosts.get('testhost')
        assert centos.repository_url_part(self.module) == output

    def test_rpm_dist(self, distro, release, codename, output):
        fake_get_connection = self.make_fake_connection((distro, release, codename))
        with patch('ceph_deploy.hosts.get_connection', fake_get_connection):
            self.module = hosts.get('testhost')
        assert centos.rpm_dist(self.module) == output
