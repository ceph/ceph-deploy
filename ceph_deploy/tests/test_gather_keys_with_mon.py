from ceph_deploy import gatherkeys
from ceph_deploy import new
import mock
import json
import copy


remoto_process_check_success_output = {
        "name": "ceph-node1",
        "rank": 0,
        "state": "leader",
        "election_epoch": 6,
        "quorum": [
            0,
            1,
            2
        ],
        "outside_quorum": [],
        "extra_probe_peers": [
            "192.168.99.125:6789\/0",
            "192.168.99.126:6789\/0"
        ],
        "sync_provider": [],
        "monmap": {
            "epoch": 1,
            "fsid": "4dbee7eb-929b-4f3f-ad23-8a4e47235e40",
            "modified": "2016-04-11 05:35:21.665220",
            "created": "2016-04-11 05:35:21.665220",
            "mons": [
                {
                    "rank": 0,
                    "name": "host0",
                    "addr": "192.168.99.124:6789\/0"
                },
                {
                    "rank": 1,
                    "name": "host1",
                    "addr": "192.168.99.125:6789\/0"
                },
                {
                    "rank": 2,
                    "name": "host2",
                    "addr": "192.168.99.126:6789\/0"
                }
            ]
        }
    }


class mock_remote_module(object):
    def get_file(self, path):
        return self.get_file_result

    def shortname(self):
        hostname_split = self.longhostname.split('.')
        return hostname_split[0]

class mock_conn(object):
    def __init__(self):
        self.remote_module = mock_remote_module()


class mock_distro(object):
    def __init__(self):
        self.conn = mock_conn()
        

def mock_hosts_get_file_key_content(host, **kwargs):
    output = mock_distro()
    mon_keyring = '[mon.]\nkey = %s\ncaps mon = allow *\n' % new.generate_auth_key()
    output.conn.remote_module.get_file_result = mon_keyring
    output.conn.remote_module.longhostname = host
    return output


def mock_hosts_get_file_key_content_none(host, **kwargs):
    output = mock_distro()
    output.conn.remote_module.get_file_result = None
    output.conn.remote_module.longhostname = host
    return output


def mock_gatherkeys_missing_success(args, distro, rlogger, path_keytype_mon, keytype, dest_dir):
    return True


def mock_gatherkeys_missing_fail(args, distro, rlogger, path_keytype_mon, keytype, dest_dir):
    return False


def mock_remoto_process_check_success(conn, args):
    out = json.dumps(remoto_process_check_success_output,sort_keys=True, indent=4)
    return out.split('\n'), "", 0


def mock_remoto_process_check_rc_error(conn, args):
    return [""], ["this failed\n"], 1


def mock_remoto_process_check_out_not_json(conn, args):
    return ["}bad output{"], [""], 0


def mock_remoto_process_check_out_missing_quorum(conn, args):
    outdata = copy.deepcopy(remoto_process_check_success_output)
    del outdata["quorum"]
    out = json.dumps(outdata,sort_keys=True, indent=4)
    return out.split('\n'), "", 0


def mock_remoto_process_check_out_missing_quorum_1(conn, args):
    outdata = copy.deepcopy(remoto_process_check_success_output)
    del outdata["quorum"][1]
    out = json.dumps(outdata,sort_keys=True, indent=4)
    return out.split('\n'), "", 0


def mock_remoto_process_check_out_missing_monmap(conn, args):
    outdata = copy.deepcopy(remoto_process_check_success_output)
    del outdata["monmap"]
    out = json.dumps(outdata,sort_keys=True, indent=4)
    return out.split('\n'), "", 0


def mock_remoto_process_check_out_missing_mons(conn, args):
    outdata = copy.deepcopy(remoto_process_check_success_output)
    del outdata["monmap"]["mons"]
    out = json.dumps(outdata,sort_keys=True, indent=4)
    return out.split('\n'), "", 0


def mock_remoto_process_check_out_missing_monmap_host1(conn, args):
    outdata = copy.deepcopy(remoto_process_check_success_output)
    del outdata["monmap"]["mons"][1]
    out = json.dumps(outdata,sort_keys=True, indent=4)
    return out.split('\n'), "", 0


class TestGatherKeysWithMon(object):
    """
    Test gatherkeys_with_mon function
    """
    def setup(self):
        self.args = mock.Mock()
        self.args.cluster = "ceph"
        self.args.mon = ['host1']
        self.host = 'host1'
        self.test_dir = '/tmp'


    @mock.patch('ceph_deploy.gatherkeys.gatherkeys_missing', mock_gatherkeys_missing_success)
    @mock.patch('ceph_deploy.lib.remoto.process.check', mock_remoto_process_check_success)
    @mock.patch('ceph_deploy.hosts.get', mock_hosts_get_file_key_content)
    def test_success(self):
        rc = gatherkeys.gatherkeys_with_mon(self.args, self.host, self.test_dir)
        assert rc is True


    @mock.patch('ceph_deploy.gatherkeys.gatherkeys_missing', mock_gatherkeys_missing_success)
    @mock.patch('ceph_deploy.lib.remoto.process.check', mock_remoto_process_check_success)
    @mock.patch('ceph_deploy.hosts.get', mock_hosts_get_file_key_content_none)
    def test_monkey_none(self):
        rc = gatherkeys.gatherkeys_with_mon(self.args, self.host, self.test_dir)
        assert rc is False


    @mock.patch('ceph_deploy.gatherkeys.gatherkeys_missing', mock_gatherkeys_missing_fail)
    @mock.patch('ceph_deploy.lib.remoto.process.check', mock_remoto_process_check_success)
    @mock.patch('ceph_deploy.hosts.get', mock_hosts_get_file_key_content)
    def test_missing_fail(self):
        rc = gatherkeys.gatherkeys_with_mon(self.args, self.host, self.test_dir)
        assert rc is False


    @mock.patch('ceph_deploy.gatherkeys.gatherkeys_missing', mock_gatherkeys_missing_success)
    @mock.patch('ceph_deploy.lib.remoto.process.check', mock_remoto_process_check_rc_error)
    @mock.patch('ceph_deploy.hosts.get', mock_hosts_get_file_key_content)
    def test_remoto_process_check_rc_error(self):
        rc = gatherkeys.gatherkeys_with_mon(self.args, self.host, self.test_dir)
        assert rc is False


    @mock.patch('ceph_deploy.gatherkeys.gatherkeys_missing', mock_gatherkeys_missing_success)
    @mock.patch('ceph_deploy.lib.remoto.process.check', mock_remoto_process_check_out_not_json)
    @mock.patch('ceph_deploy.hosts.get', mock_hosts_get_file_key_content)
    def test_remoto_process_check_out_not_json(self):
        rc = gatherkeys.gatherkeys_with_mon(self.args, self.host, self.test_dir)
        assert rc is False

    @mock.patch('ceph_deploy.gatherkeys.gatherkeys_missing', mock_gatherkeys_missing_success)
    @mock.patch('ceph_deploy.lib.remoto.process.check', mock_remoto_process_check_out_missing_quorum)
    @mock.patch('ceph_deploy.hosts.get', mock_hosts_get_file_key_content)
    def test_remoto_process_check_out_missing_quorum(self):
        rc = gatherkeys.gatherkeys_with_mon(self.args, self.host, self.test_dir)
        assert rc is False


    @mock.patch('ceph_deploy.gatherkeys.gatherkeys_missing', mock_gatherkeys_missing_success)
    @mock.patch('ceph_deploy.lib.remoto.process.check', mock_remoto_process_check_out_missing_quorum_1)
    @mock.patch('ceph_deploy.hosts.get', mock_hosts_get_file_key_content)
    def test_remoto_process_check_out_missing_quorum_1(self):
        rc = gatherkeys.gatherkeys_with_mon(self.args, self.host, self.test_dir)
        assert rc is False


    @mock.patch('ceph_deploy.gatherkeys.gatherkeys_missing', mock_gatherkeys_missing_success)
    @mock.patch('ceph_deploy.lib.remoto.process.check', mock_remoto_process_check_out_missing_mons)
    @mock.patch('ceph_deploy.hosts.get', mock_hosts_get_file_key_content)
    def test_remoto_process_check_out_missing_mon(self):
        rc = gatherkeys.gatherkeys_with_mon(self.args, self.host, self.test_dir)
        assert rc is False


    @mock.patch('ceph_deploy.gatherkeys.gatherkeys_missing', mock_gatherkeys_missing_success)
    @mock.patch('ceph_deploy.lib.remoto.process.check', mock_remoto_process_check_out_missing_monmap_host1)
    @mock.patch('ceph_deploy.hosts.get', mock_hosts_get_file_key_content)
    def test_remoto_process_check_out_missing_monmap_host1(self):
        rc = gatherkeys.gatherkeys_with_mon(self.args, self.host, self.test_dir)
        assert rc is False
