import ceph_deploy.rgw as rgw


def test_rgw_prefix_auto():
    daemon = rgw.colon_separated("hostname")
    assert daemon == ("hostname", "rgw.hostname", '7480')


def test_rgw_prefix_custom():
    daemon = rgw.colon_separated("hostname:mydaemon")
    assert daemon == ("hostname", "mydaemon", '7480')


def test_rgw_prefix_custom_port():
    daemon = rgw.colon_separated("hostname:mydaemon:7481")
    assert daemon == ("hostname", "mydaemon", '7481')
