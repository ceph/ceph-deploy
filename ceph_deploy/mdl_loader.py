import rdbms as model
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

from v_pools import mdl_updater

# use in-memory database
databaseConnectionString = 'sqlite://'


class mdl_controler(object):
    def __init__(self,args,**kwargs):
        connection = kwargs.get('connection', 'sqlite://')
        sql_log = kwargs.get('sql_log', False)
        self.args = args
        self.log = logging.getLogger("db_controler")

        self.engine = create_engine(connection, echo=sql_log)
        model.init(self.engine)
        self.SessionFactory = sessionmaker(bind=self.engine)


    def cfg_update(self,cfg):
        Session = self.SessionFactory()
        fsid = cfg.safe_get('global', 'fsid')
        matching_clusters = Session.query(model.Cluster).\
            filter(model.Cluster.identifier == fsid).\
            filter(model.Cluster.name == self.args.cluster)
        if matching_clusters.count() == 0:
            cluster = model.Cluster(
                identifier = fsid,
                name=self.args.cluster
                )
            Session.add(cluster)
            Session.commit()
            matching_clusters = Session.query(model.Cluster).\
                filter(model.Cluster.identifier == fsid)
        cluster = matching_clusters.one()

        initial_mon = cfg.safe_get('global', 'mon_initial_members')
        for host in initial_mon.split(','):
            matching_node = Session.query(model.Node).\
                filter(model.NodeHostName.hostname == host).\
                filter(model.Node.id == model.NodeHostName.node)
            if matching_node.count() == 0:
                node = model.Node()
                Session.add(node)
                Session.commit()
                node_hostname = model.NodeHostName(
                    node=node.id,
                    hostname=host
                    )
                Session.add(node_hostname)
                Session.commit()
                matching_node = Session.query(model.Node).\
                    filter(model.NodeHostName.hostname == host).\
                    filter(model.Node.id == model.NodeHostName.node)
            # now we should make sure all nodes have a service instance associated.
            for wnode in matching_node:
                matching_mon = Session.query(model.InstanceMon).\
                    filter(model.InstanceMon.node == wnode.id)
                if 0 == matching_mon.count():
                    mon_instance = model.InstanceMon(
                        node = wnode.id,
                        cluster = cluster.id,
                        )
                    Session.add(mon_instance)
                    Session.commit()


    def mon_update(self):
        view = mdl_updater(SessionFactory=self.SessionFactory,
            args= self.args)
        view.mon_update()
