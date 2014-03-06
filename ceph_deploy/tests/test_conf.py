from cStringIO import StringIO
from ceph_deploy import conf


def test_simple():
    f = StringIO("""\
[foo]
bar = baz
""")
    cfg = conf.ceph.parse(f)
    assert cfg.get('foo', 'bar') == 'baz'


def test_indent_space():
    f = StringIO("""\
[foo]
        bar = baz
""")
    cfg = conf.ceph.parse(f)
    assert cfg.get('foo', 'bar') == 'baz'


def test_indent_tab():
    f = StringIO("""\
[foo]
\tbar = baz
""")
    cfg = conf.ceph.parse(f)
    assert cfg.get('foo', 'bar') == 'baz'


def test_words_underscore():
    f = StringIO("""\
[foo]
bar_thud = baz
""")
    cfg = conf.ceph.parse(f)
    assert cfg.get('foo', 'bar_thud') == 'baz'
    assert cfg.get('foo', 'bar thud') == 'baz'


def test_words_space():
    f = StringIO("""\
[foo]
bar thud = baz
""")
    cfg = conf.ceph.parse(f)
    assert cfg.get('foo', 'bar_thud') == 'baz'
    assert cfg.get('foo', 'bar thud') == 'baz'


def test_words_many():
    f = StringIO("""\
[foo]
bar__ thud   quux = baz
""")
    cfg = conf.ceph.parse(f)
    assert cfg.get('foo', 'bar_thud_quux') == 'baz'
    assert cfg.get('foo', 'bar thud quux') == 'baz'

def test_write_words_underscore():
    cfg = conf.ceph.CephConf()
    cfg.add_section('foo')
    cfg.set('foo', 'bar thud quux', 'baz')
    f = StringIO()
    cfg.write(f)
    f.reset()
    assert f.readlines() == ['[foo]\n', 'bar_thud_quux = baz\n','\n']
