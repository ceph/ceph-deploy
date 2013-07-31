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
