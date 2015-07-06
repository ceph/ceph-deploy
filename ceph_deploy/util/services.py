import logging
from ceph_deploy.lib import remoto


init_types_available = set([ "systemd" , "sysV"])

def Property(func):
    return property(**func())

class init_exception(Exception):
    """Base class for exceptions in this module."""
    pass

class init_exception_init_type(init_exception):
    """Exception raised for errors in the init_type
    Attributes:
        msg  -- explanation of the error
    """
    def __init__(self, msg):
        self.msg = msg

class init_exception_service(init_exception):
    """Exception raised for errors in the init_type
    Attributes:
        msg  -- explanation of the error
    """
    def __init__(self, msg):
        self.msg = msg


class init_system(object):
    def __init__(self, **kwargs):
        self.log = logging.getLogger("init_system_facade")
        init_type = kwargs.get('init_type', None)
        if init_type != None:
            self.init_type = init_type
        self.connection = kwargs.get('connection', None)
        self.service_name_mapping = kwargs.get('service_name_mapping', None)

    @Property
    def init_type():
        doc = "Ouput init_type"
        def fget(self):
            if hasattr(self, '_init_type_name'):
                return self._init_type_name
            else:
                return None
        def fset(self, name):
            if not name in init_types_available:
                del(self._init_type_implementation)
                del(self._init_type_name)
                raise init_exception_init_type("Invalid Value:%s" % (name))
            self._init_type_name = name
            init_implementation = {'systemd' : init_system_systemd,
                'message' : init_system_sysV,
            }
            new_implementation = init_implementation[name]()
            new_implementation.connection = self.connection
            new_implementation.service_name_mapping = self.service_name_mapping
            self._init_type_implementation = new_implementation
            return self._init_type_name
        def fdel(self):
            del (self._init_type_implementation)
            del (self._init_type_name)
        return locals()

    @Property
    def connection():
        doc = "connection object"
        def fget(self):
            if hasattr(self, '_init_type_implementation'):
                if hasattr(self._init_type_implementation,'connection'):
                    return self._init_type_implementation.connection
            if hasattr(self, '_connection'):
                return self._connection
            return None

        def fset(self, name):
            self._connection = name
            if hasattr(self, '_init_type_implementation'):
                self._init_type_implementation.connection = name

        def fdel(self):
            del self._connection
            if hasattr(self, '_init_type_implementation'):
                if hasattr(self._init_type_implementation, "connection"):
                    del self._init_type_implementation.connection
        return locals()

    @Property
    def service_name_mapping():
        doc = """service_name_mapping
        function to translate an abstract service name to the real service name
        """
        def fget(self):
            if hasattr(self, '_init_type_implementation'):
                if hasattr(self._init_type_implementation,'service_name_mapping'):
                    return self._init_type_implementation.service_name_mapping
            if hasattr(self, '_service_name_mapping'):
                return self._service_name_mapping
            return None

        def fset(self, name):
            self._service_name_mapping = name
            if hasattr(self, '_init_type_implementation'):
                self._init_type_implementation.service_name_mapping = name

        def fdel(self):
            del self._service_name_mapping
            if hasattr(self, '_init_type_implementation'):
                if hasattr(self._init_type_implementation, "service_name_mapping"):
                    del self._init_type_implementation.service_name_mapping
        return locals()




    def _check_properties(self):
        if not hasattr(self, '_init_type_implementation'):
            raise init_exception_init_type("Property 'init_type' has invalid value.")
    def _get_service_mapped_name(self, service_name):
        if self.service_name_mapping == None:
            return service_name
        return self.service_name_mapping(service_name)

    def status(self, service_name, paramters = []):
        """Get the service status
        return:
        True for running
        False for not running
        """
        self._check_properties()
        return self._init_type_implementation.status(
            self.service_name_mapping(service_name),
            paramters)

    def start(self, service_name, paramters = []):
        """Start service
        throws exception on failure:
        """
        self._check_properties()
        return self._init_type_implementation.start(
            self.service_name_mapping(service_name),
            paramters)

    def stop(self, service_name, paramters = []):
        self._check_properties()
        return self._init_type_implementation.stop(
            self.service_name_mapping(service_name),
            paramters)

    def enable(self, service_name, paramters = []):
        self._check_properties()
        return self._init_type_implementation.enable(
            self.service_name_mapping(service_name),
            paramters)

    def disable(self, service_name, paramters = []):
        self._check_properties()
        return self._init_type_implementation.disable(
            self.service_name_mapping(service_name),
            paramters)

class init_system_systemd():

    def _get_systemctl_name(self, service_name, paramters = []):
        if len(paramters) > 0:
            return service_name + "@" + "".join(paramters)
        return service_name

    def status(self, service_name, paramters = []):
        systemctl_name = self._get_systemctl_name(service_name, paramters)
        stdout, stderr, rc = remoto.process.check(
            self.connection,
            [
                'systemctl',
                'status',
                systemctl_name,
                '--output',
                'json'
            ],
            timeout=7
        )
        if rc != 0:
            raise init_exception_service("failed to get status")
        return True

    def start(self, service_name, paramters = []):
        systemctl_name = self._get_systemctl_name(service_name, paramters)
        stdout, stderr, rc = remoto.process.check(
            self.connection,
            [
                'systemctl',
                'start',
                systemctl_name
            ],
            timeout=7
        )
        if rc != 0:
            raise init_exception_service("failed to start %s" % (service_name))
        return True

    def stop(self, service_name, paramters = []):
        systemctl_name = self._get_systemctl_name(service_name, paramters)
        stdout, stderr, rc = remoto.process.check(
            self.connection,
            [
                'systemctl',
                'stop',
                systemctl_name
            ],
            timeout=7
        )
        if rc != 0:
            raise init_exception_service("failed to get status")
        return True


    def enable(self, service_name, paramters = []):
        systemctl_name = self._get_systemctl_name(service_name, paramters)
        stdout, stderr, rc = remoto.process.check(
            self.connection,
            [
                'systemctl',
                'enable',
                systemctl_name
            ],
            timeout=7
        )

    def disable(self, service_name, paramters = []):
        systemctl_name = self._get_systemctl_name(service_name, paramters)
        rc, stdout, stderr = remoto.process.check(
            self.connection,
            [
                'systemctl',
                'disable',
                systemctl_name
            ],
            timeout=7
        )

class init_system_sysV():
    # TODO: this is largely untested
    def start(self, service_name, paramters = []):
        remoto.process.run(
            self.connection,
            [
                'service',
                service_name,
                'start'
            ],
            timeout=7
        )


    def stop(self, service_name, paramters = []):
        remoto.process.run(
            self.connection,
            [
                'service',
                service_name,
                'stop'

            ],
            timeout=7
        )


    def enable(self, service_name, paramters = []):
        remoto.process.run(
                self.connection,
                [
                    'chkconfig',
                    service_name,
                    'on'
                ],
                timeout=7
            )

    def disable(self, service_name, paramters = []):
        remoto.process.run(
                self.connection,
                [
                    'chkconfig',
                    service_name,
                    'off'
                ],
                timeout=7
            )
