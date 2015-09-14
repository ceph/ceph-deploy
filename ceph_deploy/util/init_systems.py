from ceph_deploy.lib import remoto


SYSV_SERVICES = {
    'ceph-mon': 'mon',
    'ceph-osd': 'osd',
    'ceph-osd': 'osd',
    'ceph-mds': 'mds'
}


class InitSystem(object):
    """
    Base class for all Init systems
    """

    def __init__(self, remote_conn):
        self.remote_info = remote_conn
        self.remote_conn = remote_conn.conn
        self.hostname = self.remote_conn.remote_module.shortname()

    def _run(self, cmd, **kw):
        if 'timeout' not in kw:
            kw['timeout'] = 7
        remoto.process.run(
            self.remote_conn,
            cmd,
            **kw
        )

    def start(self, service, **kw):
        """Start service on remote node"""
        raise NotImplementedError()

    def enable(self, service, **kw):
        """Enable service on remote node"""
        raise NotImplementedError()


class SysV(InitSystem):
    """
    SysV Init System
    """

    name = 'sysvinit'

    def __init__(self, remote_conn):
        super(SysV, self).__init__(remote_conn)
        self.service_exe = self.remote_conn.remote_module.which_service()

    def start(self, service, **kw):
        cluster = kw.pop('cluster', 'ceph')
        self._run(
            [
                self.service_exe,
                'ceph',
                '-c',
                '/etc/ceph/{cluster}.conf'.format(cluster=cluster),
                'start',
                '{service}.{hostname}'.format(
                    service=SYSV_SERVICES[service],
                    hostname=self.hostname
                )
            ]
        )

    def enable(self, service, **kw):
        self._run(
            [
                'chkconfig',
                'ceph',
                'on'
            ]
        )


class Upstart(InitSystem):
    """
    Upstart Init System
    """

    name = 'upstart'

    def start(self, service, **kw):
        cluster = kw.pop('cluster', 'ceph')
        self._run(
            [
                'initctl',
                'emit',
                '{service}'.format(service=service),
                'cluster={cluster}'.format(cluster=cluster),
                'id={hostname}'.format(hostname=self.hostname)
            ]
        )

    def enable(self, service, **kw):
        pass


class SystemD(InitSystem):
    """
    SystemD Init System
    """

    name = 'systemd'

    def start(self, service, **kw):
        name = kw.pop('name', self.hostname)
        self._run(
            [
                'systemctl',
                'start',
                '{service}@{name}'.format(service=service, name=name),
            ]
        )

    def enable(self, service, **kw):
        name = kw.pop('name', self.hostname)
        for instance in ['{service}@{name}'.format(service=service, name=name), 'ceph.target']:
            self._run(
                [
                    'systemctl',
                    'enable',
                    instance
                ]
            )
