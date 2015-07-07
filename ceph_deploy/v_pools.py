import rdbms as model
import logging
import json
from ceph_deploy import hosts
from ceph_deploy.lib import remoto

# pool tools
LOG = logging.getLogger(__name__)

def pool_list(conn):
    stdout, stderr, rc = remoto.process.check(
        conn,
        [
            'ceph',
            '-f',
            'json',
            'osd',
            'lspools'
            ],
        )
    if rc != 0:
        LOG.debug("stdout=%s" % (stdout))
        LOG.debug("stderr=%s" % (stderr))
        LOG.debug("rc=%s" % (rc))
        return None
    auth = json.loads("".join(stdout).strip())
    return auth

def pool_add(conn, name, number):
    stdout, stderr, rc = remoto.process.check(
        conn,
        [
            'ceph',
            'osd',
            'pool',
            'create',
            name,
            str(number)
            ],
        )
    if rc != 0:
        LOG.debug("stdout=%s" % (stdout))
        LOG.debug("stderr=%s" % (stderr))
        LOG.debug("rc=%s" % (rc))
        return None

def pool_del(conn, name):
    stdout, stderr, rc = remoto.process.check(
        conn,
        [
            'ceph',
            'osd',
            'pool',
            'delete',
            name,
            name,
            '--yes-i-really-really-mean-it'
            ],
        )
    if rc != 0:
        LOG.debug("stdout=%s" % (stdout))
        LOG.debug("stderr=%s" % (stderr))
        LOG.debug("rc=%s" % (rc))
        return None


class mdl_updater(object):
    def __init__(self,**kwargs):
        self.SessionFactory = kwargs.get('SessionFactory', None)
        self.args = kwargs.get('args', None)
        self.distro = None
        self.clusterId = None

    def connect(self,clusterId):
        self.clusterId = clusterId
        LOG.info("clusterId=%s" % (clusterId))
        Session = self.SessionFactory()
        cluster_qry = Session.query(model.Cluster).\
            filter(model.Cluster.identifier == clusterId)
        if cluster_qry.count() == 0:
            LOG.warning("Cluster '%s' does not have any known mon services" % (
                clusterId,
                ))
            return False
        cluster = cluster_qry.one()
        possible_mons = Session.query(model.NodeHostName).\
            filter(model.InstanceMon.cluster == cluster.id).\
            filter(model.InstanceMon.node == model.Node.id).\
            filter(model.NodeHostName.node == model.Node.id)
        if possible_mons.count() == 0:
            LOG.warning("Cluster '%s' with fsid '%s' does not have any known mon services" % (
                cluster.name,
                cluster.identifier
                ))
            return False
        distro = None
        # find the first mon we can connect too,
        # it does not matter which
        for mon in possible_mons:
            try:
                distro = hosts.get(mon.hostname, username=self.args.username)
            except:
                # try next host
                LOG.warning("Failed to connect to '%s' with username '%s'\n" % (
                    mon.hostname,
                    self.args.username,
                    ))
                return False
            break
        distro = hosts.get(mon.hostname, username=self.args.username)
        if distro == None:
            LOG.warning("No mon providing node in cluster '%s' with fsid '%s' could not be accessed" % (
                cluster.name,
                cluster.identifier
                ))
            return False
        self.conn = distro.conn

    def mon_update_pool_list(self):
        """
        Update model with information gathered about
        a mon on each cluster known
        """
        Session = self.SessionFactory()
        
        actor_name = "mon_update_pool_list"
        
        actor_qry = Session.query(model.UpdateActor).\
                filter(model.UpdateActor.name == actor_name)
        if actor_qry.count() == 0:
            new_actor = model.UpdateActor(
                name=actor_name
            )
            Session.add(new_actor)
            Session.commit()
            actor_qry = Session.query(model.UpdateActor).\
                filter(model.UpdateActor.name == actor_name)
        actor = actor_qry.one()
        
        update = model.Update(
            actor=actor.id
            )
        Session.add(update)
        Session.commit()
        
        cluster_qry = Session.query(model.Cluster)
        if cluster_qry.count() == 0:
            return False
        for cluster in cluster_qry:
            possible_mons = Session.query(model.NodeHostName).\
                filter(model.InstanceMon.cluster == cluster.id).\
                filter(model.InstanceMon.node == model.Node.id).\
                filter(model.NodeHostName.node == model.Node.id)
            if possible_mons.count() == 0:
                LOG.warning("Cluster '%s' with fsid '%s' does not have any known mon services" % (
                    cluster.name,
                    cluster.identifier
                    ))
                continue
            distro = None
            # find the first mon we can connect too,
            # it does not matter which
            for mon in possible_mons:
                try:
                    distro = hosts.get(mon.hostname, username=self.args.username)
                except:
                    # try next host
                    LOG.warning("Failed to connect to '%s' with username '%s'\n" % (
                        mon.hostname,
                        self.args.username,
                        ))
                    continue
                break
            distro = hosts.get(mon.hostname, username=self.args.username)
            if distro == None:
                LOG.warning("No mon providing node in cluster '%s' with fsid '%s' could not be accessed" % (
                    cluster.name,
                    cluster.identifier
                    ))
                continue
            poollist = pool_list(distro.conn)
            for pool in poollist:
                pool_qry = Session.query(model.Pool).\
                    filter(model.Pool.cluster == cluster.id).\
                    filter(model.Pool.num == pool["poolnum"]).\
                    filter(model.Pool.name == pool["poolname"])

                if 0 == pool_qry.count():
                    newpool = model.Pool(
                            num = pool["poolnum"],
                            name = pool["poolname"],
                            cluster = 1,
                            created = update.id
                            
                        )
                    Session.add(newpool)
                    Session.commit()


    def mon_update(self, **kwargs):
        Session = self.SessionFactory()
        self.mon_update_pool_list()
        cluster_qry = Session.query(model.Cluster)
        ident_list = []
        for clusterId in cluster_qry:
            LOG.info("with cluster id:%s" % (clusterId))
            identifier = (clusterId)
            ident_list.append(identifier)
        identifier = ident_list.pop()
        self.mon_update_pools_required()



    def mon_update_pools_required(self):
        if self.distro == None:
            LOG.info("not installing required pools id:%s" % (self.clusterId))
            return
        conn = self.distro.conn
        requiredPools = set([".rgw",
                ".rgw.control",
                ".rgw.gc",
                ".log",
                ".intent-log",
                ".usage",
                ".users",
                ".users.email",
                ".users.swift",
                ".users.uid"
            ])
        allpools = pool_list(conn)
        foundnames = set()
        foundnumbers = set()
        for pool in allpools:
            name = pool[u'poolname']
            number = pool[u'poolnum']
            foundnames.add(name)
            foundnumbers.add(number)
        counter = 0
        for name in requiredPools.difference(foundnames):
            while counter in foundnumbers:
                counter = counter + 1
            foundnumbers.add(counter)
            pool_add(conn, name, counter)
