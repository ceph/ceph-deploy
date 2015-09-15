from ceph_deploy.lib import remoto

# Provide mappings/translations for services depending
# on Init system.  All services coming into the classes
# here should be one of ceph-mon, ceph-osd, ceph-mds, or
# ceph-radosgw. It's then up to the code here to Do The
# Right Thing.
SYSV_SERVICES = {
    'ceph-mon': 'mon',
    'ceph-mds': 'mds'
}

UPSTART_SERVICES = {
    'ceph-radosgw': 'radosgw'
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
        name = kw.pop('name', self.hostname)
        init_script = 'ceph-radosgw' if service == 'ceph-radosgw' else 'ceph'
        self._run(
            [
                self.service_exe,
                init_script,
                '-c',
                '/etc/ceph/{cluster}.conf'.format(cluster=cluster),
                'start',
                '{service}.{name}'.format(
                    service=SYSV_SERVICES.get(service, service),
                    name=name
                )
            ]
        )

    def enable(self, service, **kw):
        init_script = 'ceph-radosgw' if service == 'ceph-radosgw' else 'ceph'
        self._run(
            [
                'chkconfig',
                init_script,
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
        name = kw.pop('name', self.hostname)
        self._run(
            [
                'initctl',
                'emit',
                '{service}'.format(
                    service=UPSTART_SERVICES.get(service, service)
                ),
                'cluster={cluster}'.format(cluster=cluster),
                'id={name}'.format(name=name)
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
        services = ['ceph.target']
        if service != "ceph-osd":
            services.append('{service}@{name}'.format(service=service, name=name))
        for instance in services:
            self._run(
                [
                    'systemctl',
                    'enable',
                    instance
                ]
            )
