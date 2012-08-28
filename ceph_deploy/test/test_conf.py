from cStringIO import StringIO
from .. import conf


def test_simple():
    f = StringIO("""\
[foo]
bar = baz
""")
    cfg = conf.parse(f)
    assert cfg.get('foo', 'bar') == 'baz'


def test_indent_space():
    f = StringIO("""\
[foo]
        bar = baz
""")
    cfg = conf.parse(f)
    assert cfg.get('foo', 'bar') == 'baz'


def test_indent_tab():
    f = StringIO("""\
[foo]
\tbar = baz
""")
    cfg = conf.parse(f)
    assert cfg.get('foo', 'bar') == 'baz'
