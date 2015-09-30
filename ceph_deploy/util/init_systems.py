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
        self._hostname = None

    @property
    def hostname(self):
        if not self._hostname:
            self._hostname = self.remote_conn.remote_module.shortname()
        return self._hostname

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
        self._service_exe = None

    @property
    def service_exe(self):
        if not self._service_exe:
            self._service_exe = self.remote_conn.remote_module.which_service()
        return self._service_exe

    def _get_init_script(self, service):
        return 'ceph-radosgw' if service == 'ceph-radosgw' else 'ceph'

    def _build_service_command(
        self, service, action, daemon_name, cluster_name=None
    ):
        init_script = self._get_init_script(service)
        cmd = [
            self.service_exe,
            init_script,
        ]
        if action == 'start' and init_script == 'ceph':
            cmd.extend(
                [
                    '-c',
                    '/etc/ceph/{cluster}.conf'.format(cluster=cluster_name),
                ]
            )
        cmd.append('{action}'.format(action=action))
        if init_script == 'ceph':
            cmd.extend(
                [
                    '{service}.{name}'.format(
                        service=SYSV_SERVICES.get(service, service),
                        name=daemon_name
                    )
                ]
            )
        return cmd

    def start(self, service, **kw):
        cluster = kw.pop('cluster', 'ceph')
        name = kw.pop('name', self.hostname)
        cmd = self._build_service_command(
                service, 'start', name, cluster_name=cluster
        )
        self._run(cmd)

    def enable(self, service, **kw):
        init_script = self._get_init_script(service)
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
