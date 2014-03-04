from mock import MagicMock


def fake_getaddrinfo(*a, **kw):
    return_host = kw.get('return_host', 'host1')
    return [[0,0,0,0, return_host]]


def mock_open(mock=None, data=None):
    """
    Fake the behavior of `open` when used as a context manager
    """
    if mock is None:
        mock = MagicMock(spec=file)

    handle = MagicMock(spec=file)
    handle.write.return_value = None
    if data is None:
        handle.__enter__.return_value = handle
    else:
        handle.__enter__.return_value = data
    mock.return_value = handle
    return mock



