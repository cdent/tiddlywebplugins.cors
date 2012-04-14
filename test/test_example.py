def test_compile():
    try:
        import tiddlywebplugins.cors
    except ImportError, exc:
        assert False, 'unable to import tiddlywebplugins.cors: %s' % exc
