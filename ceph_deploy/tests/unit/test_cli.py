from ceph_deploy import cli
from ceph_deploy.tests import util


class FakeLogger(object):

    def __init__(self):
        self._calls = []
        self._info = []

    def _output(self):
        return '\n'.join(self._calls)

    def _record(self, level, message):
        self._calls.append(message)
        method = getattr(self, '_%s' % level)
        method.append(message)

    def info(self, message):
        self._record('info', message)


class TestLogFlags(object):

    def setup(self):
        self.logger = FakeLogger()

    def test_logs_multiple_object_attributes(self):
        args = util.Empty(verbose=True, adjust_repos=False)
        cli.log_flags(args, logger=self.logger)
        result = self.logger._output()
        assert ' verbose ' in result
        assert ' adjust_repos ' in result

    def test_attributes_are_logged_with_values(self):
        args = util.Empty(verbose=True)
        cli.log_flags(args, logger=self.logger)
        result = self.logger._output()
        assert ' verbose ' in result
        assert ' : True' in result

    def test_private_attributes_are_not_logged(self):
        args = util.Empty(verbose=True, _private='some value')
        cli.log_flags(args, logger=self.logger)
        result = self.logger._output()
        assert ' _private ' not in result
