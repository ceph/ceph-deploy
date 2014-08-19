import socket
from mock import Mock
from argparse import ArgumentError
from pytest import raises

from ceph_deploy.util import arg_validators


class TestRegexMatch(object):

    def test_match_raises(self):
        validator = arg_validators.RegexMatch(r'\d+')
        with raises(ArgumentError):
            validator('1')

    def test_match_passes(self):
        validator = arg_validators.RegexMatch(r'\d+')
        assert validator('foo') == 'foo'

    def test_default_error_message(self):
        validator = arg_validators.RegexMatch(r'\d+')
        with raises(ArgumentError) as error:
            validator('1')
        message = error.value.message
        assert message == 'must match pattern \d+'

    def test_custom_error_message(self):
        validator = arg_validators.RegexMatch(r'\d+', 'wat')
        with raises(ArgumentError) as error:
            validator('1')
        message = error.value.message
        assert message == 'wat'


class TestHostName(object):

    def setup(self):
        self.fake_sock = Mock()
        self.fake_sock.gaierror = socket.gaierror
        self.fake_sock.getaddrinfo.side_effect = socket.gaierror

    def test_hostname_is_not_resolvable(self):
        hostname = arg_validators.Hostname(self.fake_sock)
        with raises(ArgumentError) as error:
            hostname('unresolvable')
        message = error.value.message
        assert 'is not resolvable' in message

    def test_hostname_with_name_is_not_resolvable(self):
        hostname = arg_validators.Hostname(self.fake_sock)
        with raises(ArgumentError) as error:
            hostname('name:foo')
        message = error.value.message
        assert 'foo is not resolvable' in message

    def test_ip_is_allowed_when_paired_with_host(self):
        self.fake_sock = Mock()
        self.fake_sock.gaierror = socket.gaierror

        def side_effect(*args):
                # First call passes, second call raises socket.gaierror
                self.fake_sock.getaddrinfo.side_effect = socket.gaierror

        self.fake_sock.getaddrinfo.side_effect = side_effect
        hostname = arg_validators.Hostname(self.fake_sock)
        result = hostname('name:192.168.1.111')
        assert result == 'name:192.168.1.111'

    def test_ipv6_is_allowed_when_paired_with_host(self):
        self.fake_sock = Mock()
        self.fake_sock.gaierror = socket.gaierror

        def side_effect(*args):
                # First call passes, second call raises socket.gaierror
                self.fake_sock.getaddrinfo.side_effect = socket.gaierror

        self.fake_sock.getaddrinfo.side_effect = side_effect
        hostname = arg_validators.Hostname(self.fake_sock)
        result = hostname('name:2001:0db8:85a3:0000:0000:8a2e:0370:7334')
        assert result == 'name:2001:0db8:85a3:0000:0000:8a2e:0370:7334'

    def test_host_is_resolvable(self):
        self.fake_sock = Mock()
        self.fake_sock.gaierror = socket.gaierror

        def side_effect(*args):
                # First call passes, second call raises socket.gaierror
                self.fake_sock.getaddrinfo.side_effect = socket.gaierror

        self.fake_sock.getaddrinfo.side_effect = side_effect
        hostname = arg_validators.Hostname(self.fake_sock)
        result = hostname('name:example.com')
        assert result == 'name:example.com'

    def test_hostname_must_be_an_ip(self):
        self.fake_sock.getaddrinfo = Mock()
        hostname = arg_validators.Hostname(self.fake_sock)
        with raises(ArgumentError) as error:
            hostname('0')
        message = error.value.message
        assert '0 must be a hostname' in message


class TestSubnet(object):

    def test_subnet_has_less_than_four_numbers(self):
        validator = arg_validators.Subnet()

        with raises(ArgumentError) as error:
            validator('3.3.3/12')
        message = error.value.message
        assert 'at least 4 numbers' in message

    def test_subnet_has_non_digits(self):
        validator = arg_validators.Subnet()

        with raises(ArgumentError) as error:
            validator('3.3.3.a/12')
        message = error.value.message
        assert 'have digits separated by dots' in message

    def test_subnet_missing_slash(self):
        validator = arg_validators.Subnet()

        with raises(ArgumentError) as error:
            validator('3.3.3.3')
        message = error.value.message
        assert 'must contain a slash' in message
