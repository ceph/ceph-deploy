from ceph_deploy.exc import ExecutableNotFound
from ceph_deploy.lib import remoto
import os.path
import re

def executable_path(conn, executable):
    """
    Remote validator that accepts a connection object to ensure that a certain
    executable is available returning its full path if so.

    Otherwise an exception with thorough details will be raised, informing the
    user that the executable was not found.
    """
    executable_path = conn.remote_module.which(executable)
    if not executable_path:
        raise ExecutableNotFound(executable, conn.hostname)
    return executable_path


def is_systemd(conn):
    """
    Attempt to detect if a remote system is a systemd one or not
    by looking into ``/proc`` just like the ceph init script does::

        # detect systemd
        # SYSTEMD=0
        grep -qs systemd /proc/1/comm && SYSTEMD=1
    """
    return conn.remote_module.grep(
        'systemd',
        '/proc/1/comm'
    )

def systemd_defaults_clustername(conn, cluster_name):
    if not is_systemd:
        return
    sysconf_file_path = '/etc/sysconfig/ceph'
    sysconf_dir_path = os.path.dirname(sysconf_file_path)
    system_config_dir_exists = conn.remote_module.path_exists(sysconf_dir_path)
    if not system_config_dir_exists:
        conn.remote_module.safe_mkdir(sysconf_dir_path)
    system_config_exists = conn.remote_module.path_exists(sysconf_file_path)
    replacement = "CLUSTER=%s" % (cluster_name)
    find_cluster = "^CLUSTER=.*$"
    pattern = re.compile(find_cluster)
    output_lines = []
    has_replaced = False
    if system_config_exists:
        content = conn.remote_module.get_file('/etc/sysconfig/ceph')
        for line in content.split('\n'):
            stripped_line = line.strip()
            match_details = pattern.match(line)
            if match_details == None:
                output_lines.append(stripped_line)
                continue
            match_content = line[match_details.start():match_details.end()]
            if match_content == replacement:
                if not has_replaced:
                    output_lines.append(replacement)
                    has_replaced = True
                else:
                    output_lines.append("#%s" % (stripped_line))
                continue
            if has_replaced == True:
                output_lines.append("#%s" % (stripped_line))
                continue
            has_replaced = True
            output_lines.append("#%s" % (stripped_line))
            output_lines.append(replacement)

    if has_replaced == False:
        output_lines.append(replacement)
    for index in range(len(output_lines)-1 , 0,-1):
        if len(output_lines[index]) == 0:
            del(output_lines[index])
        else:
            break
    conn.remote_module.write_file(sysconf_file_path, "\n".join(output_lines) + '\n')


def enable_service(conn, service='ceph'):
    """
    Enable a service on a remote host depending on the type of init system.
    Obviously, this should be done for RHEL/Fedora/CentOS systems.

    This function does not do any kind of detection.
    """
    if is_systemd(conn):
        remoto.process.run(
            conn,
            [
                'systemctl',
                'enable',
                '{service}'.format(service=service),
            ]
        )
    else:
        remoto.process.run(
            conn,
            [
                'chkconfig',
                '{service}'.format(service=service),
                'on',
            ]
        )
