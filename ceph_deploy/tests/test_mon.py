from ceph_deploy import mon
from ceph_deploy.conf import CephConf
from mock import Mock


def make_fake_conf():
    return CephConf()

# NOTE: If at some point we re-use this helper, move it out
# and make it even more generic

def make_fake_conn(receive_returns=None):
    receive_returns = receive_returns or (['{}'], '', 0)
    conn = Mock()
    conn.return_value = conn
    conn.execute = conn
    conn.receive = Mock(return_value=receive_returns)
    conn.result = Mock(return_value=conn)
    return conn


class TestCatchCommonErrors(object):

    def setup(self):
        self.logger = Mock()

    def assert_logger_message(self, logger, msg):
        calls = logger.call_args_list
        for log_call in calls:
            if msg in log_call[0][0]:
                return True
        raise AssertionError('"%s" was not found in any of %s' % (msg, calls))

    def test_warn_if_no_intial_members(self):
        fake_conn = make_fake_conn()
        cfg = make_fake_conf()
        mon.catch_mon_errors(fake_conn, self.logger, 'host', cfg, Mock())
        expected_msg = 'is not defined in `mon initial members`'
        self.assert_logger_message(self.logger.warning, expected_msg)

    def test_warn_if_host_not_in_intial_members(self):
        fake_conn = make_fake_conn()
        cfg = make_fake_conf()
        cfg.add_section('global')
        cfg.set('global', 'mon initial members', 'AAAA')
        mon.catch_mon_errors(fake_conn, self.logger, 'host', cfg, Mock())
        expected_msg = 'is not defined in `mon initial members`'
        self.assert_logger_message(self.logger.warning, expected_msg)

    def test_warn_if_not_mon_in_monmap(self):
        fake_conn = make_fake_conn()
        cfg = make_fake_conf()
        mon.catch_mon_errors(fake_conn, self.logger, 'host', cfg, Mock())
        expected_msg = 'does not exist in monmap'
        self.assert_logger_message(self.logger.warning, expected_msg)

    def test_warn_if_not_public_addr_and_not_public_netw(self):
        fake_conn = make_fake_conn()
        cfg = make_fake_conf()
        cfg.add_section('global')
        mon.catch_mon_errors(fake_conn, self.logger, 'host', cfg, Mock())
        expected_msg = 'neither `public_addr` nor `public_network`'
        self.assert_logger_message(self.logger.warning, expected_msg)
