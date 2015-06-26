import ceph_deploy.rgw as rgw


def test_rgw_prefix_auto():
    daemon = rgw.colon_separated("hostname")
    assert daemon == ("hostname", "rgw.hostname")


def test_rgw_prefix_custom():
    daemon = rgw.colon_separated("hostname:mydaemon")
    assert daemon == ("hostname", "rgw.mydaemon")
