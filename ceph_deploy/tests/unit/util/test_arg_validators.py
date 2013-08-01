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
        self.fake_sock.gethostbyname.side_effect = socket.gaierror

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

    def test_ip_is_not_resolvable(self):
        self.fake_sock.gethostbyname = Mock(return_value='192.168.1.111')
        hostname = arg_validators.Hostname(self.fake_sock)
        with raises(ArgumentError) as error:
            hostname('name:192.168.1.111')
        message = error.value.message
        assert 'must be a hostname not an IP' in message

    def test_host_is_resolvable(self):
        self.fake_sock.gethostbyname = Mock()
        hostname = arg_validators.Hostname(self.fake_sock)
        result = hostname('name:example.com')
        assert result == 'name:example.com'
