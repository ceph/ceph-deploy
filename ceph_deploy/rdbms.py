# Note These are useful to be here for code clarity.
#from sqlalchemy import create_engine
#from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Boolean, DateTime,LargeBinary
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime
import uuid

time_format_definition = "%Y-%m-%dT%H:%M:%SZ"

Base = declarative_base()

# What makes the change to status
class UpdateActor(Base):
    __tablename__ = 'ACTOR'
    id = Column(Integer, primary_key=True)
    identifier = Column(String(50),unique=True,nullable = False)
    name = Column(String(50),unique=True,nullable = False)
    def __init__(self, **kwargs):
        identifier = kwargs.get('identifier', None)
        if identifier == None:
            identifier = str(uuid.uuid4())
        self.identifier = identifier
        self.name = kwargs.get('name', None)
        
        
# Updates to instances with status should referance update
# If the data base is to persisst.
class Update(Base):
    __tablename__ = 'UPDATE'
    id = Column(Integer, primary_key=True)
    identifier = Column(String(50),unique=True,nullable = False)
    actor = Column(Integer, ForeignKey(UpdateActor.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = False)
    created = Column(DateTime,nullable = False)
    expired = Column(DateTime,nullable = True)
    def __init__(self, **kwargs):
        identifier = kwargs.get('identifier', None)
        if identifier == None:
            identifier = str(uuid.uuid4())
        self.identifier = identifier
        dt = kwargs.get('datetime', None)
        if dt == None:
            dt = datetime.datetime.now()
        self.created = dt
        self.actor = kwargs.get('actor', None)

class InitSystem(Base):
    __tablename__ = 'INIT_SYSTEM'
    id = Column(Integer, primary_key=True)
    identifier = Column(String(50),unique=True,nullable = False)
    name = Column(String(50),unique=True,nullable = False)
    def __init__(self, **kwargs):
        identifier = kwargs.get('identifier', None)
        if identifier == None:
            identifier = str(uuid.uuid4())
        self.identifier = identifier

class OperatingSystem(Base):
    __tablename__ = 'OPERATING_SYSTEM'
    id = Column(Integer, primary_key=True)
    identifier = Column(String(50),unique=True,nullable = False)
    name = Column(String(50),nullable = False)
    version_major = Column(String(50),nullable = False)
    version_minor = Column(String(50),nullable = False)
    def __init__(self, **kwargs):
        identifier = kwargs.get('identifier', None)
        if identifier == None:
            identifier = str(uuid.uuid4())
        self.identifier = identifier

class NodeState(Base):
    __tablename__ = 'NODE_STATE'
    id = Column(Integer, primary_key=True)
    identifier = Column(String(50),unique=True,nullable = False)
    name = Column(String(50),unique=True,nullable = False)
    def __init__(self, **kwargs):
        identifier = kwargs.get('identifier', None)
        if identifier == None:
            identifier = str(uuid.uuid4())
        self.identifier = identifier


class Node(Base):
    __tablename__ = 'NODE'
    id = Column(Integer, primary_key=True)
    identifier = Column(String(50),unique=True,nullable = False)
    init = Column(Integer, ForeignKey(InitSystem.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = True)
    def __init__(self, **kwargs):
        identifier = kwargs.get('identifier', None)
        if identifier == None:
            identifier = str(uuid.uuid4())
        self.identifier = identifier


# Hosts cvan have more than one hostname.
# Linux users may disagree but this is a
# limitation of linux not *nix.
class NodeHostName(Base):
    __tablename__ = 'NODE_HOSTNAME'
    id = Column(Integer, primary_key=True)
    node = Column(Integer, ForeignKey(Node.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = False)
    hostname = Column(String(50),unique=False,nullable = False)
    def __init__(self, **kwargs):
        self.node = kwargs.get('node', None)
        self.hostname = kwargs.get('hostname', None)
    def __repr__(self):
        return "<NodeHostName('%s','%s', '%s')>" % (self.id, self.node, self.hostname)


class NodeStatus(Base):
    __tablename__ = 'NODE_STATUS'
    id = Column(Integer, primary_key=True)
    status = Column(Integer, ForeignKey(InitSystem.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = True)
    model_instance = Column(Integer, ForeignKey(InitSystem.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = True)
    created = Column(Integer, ForeignKey(Update.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = False)
    expired = Column(Integer, ForeignKey(Update.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = True)

class Cluster(Base):
    __tablename__ = 'CLUSTER'
    id = Column(Integer, primary_key=True)
    identifier = Column(String(50),unique=True,nullable = False)
    name = Column(String(50),unique=True,nullable = False)
    def __init__(self, **kwargs):
        identifier = kwargs.get('identifier', None)
        if identifier == None:
            identifier = repr(uuid.uuid4())
        self.identifier = identifier
        self.name = kwargs.get('name', None)


class Pool(Base):
    __tablename__ = 'POOL'
    id = Column(Integer, primary_key=True)
    cluster = Column(Integer, ForeignKey(Cluster.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = False)
    created = Column(Integer, ForeignKey(Update.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = False)
    expired = Column(Integer, ForeignKey(Update.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = True)
    
    num = Column(Integer, nullable = False )
    name = Column(String(50), nullable = False)
    
    def __init__(self, **kwargs):
        self.cluster = kwargs.get('cluster', None)
        self.num = kwargs.get('num', None)
        self.name = kwargs.get('name', None)
        self.created = kwargs.get('created', None)
        self.expired = kwargs.get('expired', None)

# this is where we can store tasks to do.
class ServiceState(Base):
    __tablename__ = 'SERVICE_STATE'
    id = Column(Integer, primary_key=True)
    identifier = Column(String(50),unique=True,nullable = False)
    name = Column(String(50),unique=True,nullable = True)
    # 1 == want Installed
    # 2 == Installed
    installed = Column(Integer,nullable = True)
    # 1 == Want Running
    # 2 == Running
    running = Column(Integer,nullable = True)
    # 1 == Want on Boot
    # 2 == On boot start
    enabled_on_boot = Column(Integer,nullable = True)


    def __init__(self, **kwargs):
        identifier = kwargs.get('identifier', None)
        if identifier == None:
            identifier = str(uuid.uuid4())
        self.identifier = identifier
        self.name = kwargs.get('name', None)

# this stores all the instance on mon instances
class InstanceMon(Base):
    __tablename__ = 'MON_INSTANCE'
    id = Column(Integer, primary_key=True)
    identifier = Column(String(50),unique=True,nullable = False)
    name = Column(String(50),unique=True,nullable = True)
    node = Column(Integer, ForeignKey(Node.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = False)
    cluster = Column(Integer, ForeignKey(Cluster.id, onupdate="CASCADE", ondelete="CASCADE"))
    ipv4 = Column(String(15),unique=True,nullable = True)
    ipv6 = Column(String(48),unique=True,nullable = True)
    path_bootstrap_key = Column(String(50),unique=True,nullable = True)
    path_key = Column(String(50),unique=True,nullable = True)

    def __init__(self, **kwargs):
        identifier = kwargs.get('identifier', None)
        if identifier == None:
            identifier = str(uuid.uuid4())
        self.identifier = identifier
        self.name = kwargs.get('name', None)
        self.node = kwargs.get('node', None)
        self.cluster = kwargs.get('cluster', None)

# this binds mon instance to state
class MonStatus(Base):
    __tablename__ = 'MON_STATUS'
    id = Column(Integer, primary_key=True)
    identifier = Column(String(50),unique=True,nullable = False)
    mon = Column(Integer, ForeignKey(InstanceMon.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = False)
    state = Column(Integer, ForeignKey(ServiceState.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = False)
    created = Column(Integer, ForeignKey(Update.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = False)
    expired = Column(Integer, ForeignKey(Update.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = True)
    def __init__(self, **kwargs):
        identifier = kwargs.get('identifier', None)
        if identifier == None:
            identifier = str(uuid.uuid4())
        self.identifier = identifier
        self.mon = kwargs.get('mon', None)
        self.running = kwargs.get('identifier', None)
        self.enabled_on_boot = None


class Disk(Base):
    __tablename__ = 'DISK'
    id = Column(Integer, primary_key=True)
    identifier = Column(String(50),unique=True,nullable = False)
    #1 == GPT
    #2 == MSDOS
    table = Column(Integer,nullable = True)
    node = Column(Integer, ForeignKey(Node.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = True)
    def __init__(self, **kwargs):
        identifier = kwargs.get('identifier', None)
        if identifier == None:
            identifier = str(uuid.uuid4())
        self.identifier = identifier
        self.table = kwargs.get('table', None)

class DiskPartition(Base):
    __tablename__ = 'DISK_PARTITION'
    id = Column(Integer, primary_key=True)
    identifier = Column(String(50),unique=True,nullable = False)
    def __init__(self, **kwargs):
        identifier = kwargs.get('identifier', None)
        if identifier == None:
            identifier = str(uuid.uuid4())
        self.identifier = identifier



class InstanceOsd(Base):
    __tablename__ = 'OSD_INSTANCE'
    id = Column(Integer, primary_key=True)
    identifier = Column(String(50),unique=True,nullable = False)
    name = Column(String(50),unique=True,nullable = False)
    journel = Column(Integer, ForeignKey(DiskPartition.id, onupdate="CASCADE", ondelete="CASCADE"))
    data = Column(Integer, ForeignKey(DiskPartition.id, onupdate="CASCADE", ondelete="CASCADE"))
    cluster = Column(Integer, ForeignKey(Cluster.id, onupdate="CASCADE", ondelete="CASCADE"))
    def __init__(self, **kwargs):
        identifier = kwargs.get('identifier', None)
        if identifier == None:
            identifier = str(uuid.uuid4())
        self.identifier = identifier


class OsdStatus(Base):
    __tablename__ = 'OSD_STATUS'
    id = Column(Integer, primary_key=True)
    identifier = Column(String(50),unique=True,nullable = False)
    osd = Column(Integer, ForeignKey(InstanceOsd.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = False)
    state = Column(Integer, ForeignKey(ServiceState.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = False)
    created = Column(Integer, ForeignKey(Update.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = False)
    expired = Column(Integer, ForeignKey(Update.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = True)
    def __init__(self, **kwargs):
        identifier = kwargs.get('identifier', None)
        if identifier == None:
            identifier = str(uuid.uuid4())
        self.identifier = identifier
        self.osd = kwargs.get('osd', None)
        self.running = kwargs.get('running', None)
        self.enabled_on_boot = None


class InstanceRgw(Base):
    __tablename__ = 'RGW_INSTANCE'
    id = Column(Integer, primary_key=True)
    identifier = Column(String(50),unique=True,nullable = False)
    name = Column(String(50),unique=True,nullable = True)
    node = Column(Integer, ForeignKey(Node.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = False)
    cluster = Column(Integer, ForeignKey(Cluster.id, onupdate="CASCADE", ondelete="CASCADE"))
    port = Column(Integer,nullable = True)
    created = Column(Integer, ForeignKey(Update.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = False)
    expired = Column(Integer, ForeignKey(Update.id, onupdate="CASCADE", ondelete="CASCADE"),nullable = True)
    def __init__(self, **kwargs):
        identifier = kwargs.get('identifier', None)
        if identifier == None:
            identifier = str(uuid.uuid4())
        self.identifier = identifier
        self.name = kwargs.get('name', None)
        self.node = kwargs.get('node', None)
        self.cluster = kwargs.get('cluster', None)




def init(engine):
    Base.metadata.create_all(engine)
