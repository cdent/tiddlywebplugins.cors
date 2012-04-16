"""
Test cors based on docs at
http://www.html5rocks.com/en/tutorials/cors/
"""


from wsgi_intercept import httplib2_intercept
import wsgi_intercept
import httplib2
import shutil


from tiddlyweb.config import config
from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.web.serve import load_app
from tiddlywebplugins.utils import get_store


def setup_module(module):
    try:
        shutil.rmtree('store')
    except:  # it's not there
        pass

    app = load_app()
    def app_fn():
        return app

    module.store = get_store(config)

    httplib2_intercept.install()
    wsgi_intercept.add_wsgi_intercept('0.0.0.0', 8080, app_fn)

    module.http = httplib2.Http()


def test_simple_get_no_cors():
    response, content = http.request('http://0.0.0.0:8080/')
    assert response['status'] == '200'
    assert '/bags' in content

def test_simple_get_cors():
    response, content = http.request('http://0.0.0.0:8080/',
            headers = {'Origin': 'http://example.com'})
    assert response['status'] == '200'
    assert '/bags' in content
    assert response['access-control-allow-origin'] == '*'
    assert response['access-control-expose-headers'] == 'ETag, Content-Type'

def test_simple_get_match_origin():
    config['cors.match_origin'] = True
    response, content = http.request('http://0.0.0.0:8080/',
            headers = {'Origin': 'http://example.com'})
    assert response['status'] == '200'
    assert '/bags' in content
    assert response['access-control-allow-origin'] == 'http://example.com'
    assert response['access-control-expose-headers'] == 'ETag, Content-Type'
    config['cors.match_origin'] = False

def test_simple_get_allow_auth():
    config['cors.allow_creds'] = True
    response, content = http.request('http://0.0.0.0:8080/',
            headers = {'Origin': 'http://example.com'})
    assert response['status'] == '200'
    assert '/bags' in content
    assert response['access-control-allow-origin'] == '*'
    assert response['access-control-expose-headers'] == 'ETag, Content-Type'
    assert response['access-control-allow-credentials'] == 'true'
    config['cors.allow_creds'] = False

def test_simple_custom_exposed_headers():
    config['cors.exposed_headers'] = ['Frank', 'Barney']
    response, content = http.request('http://0.0.0.0:8080/',
            headers = {'Origin': 'http://example.com'})
    assert response['status'] == '200'
    assert '/bags' in content
    assert response['access-control-allow-origin'] == '*'
    assert response['access-control-expose-headers'] == 'ETag, Content-Type, Frank, Barney'
    del config['cors.exposed_headers']

def test_not_simple_cache():
    config['cors.cache_age'] = 400
    response, content = http.request('http://0.0.0.0:8080/',
            headers = {'Origin': 'http://example.com'},
            method = 'OPTIONS')
    assert response['status'] == '200'
    assert response['access-control-allow-origin'] == 'http://example.com'
    assert response['access-control-allow-headers'] == 'ETag, Content-Type'
    assert response['access-control-max-age'] == '400'
    del config['cors.cache_age']
    response, content = http.request('http://0.0.0.0:8080/',
            headers = {'Origin': 'http://example.com'},
            method = 'OPTIONS')
    assert response['status'] == '200'
    assert response['access-control-allow-origin'] == 'http://example.com'
    assert response['access-control-allow-headers'] == 'ETag, Content-Type'
    assert response['access-control-max-age'] == '600'

def test_not_simple_no_auth():
    response, content = http.request('http://0.0.0.0:8080/bags/franny',
            method = 'OPTIONS',
            headers = {'Origin': 'http://example.com',
                'Access-Control-Request-Method': 'DELETE',
                'Access-Control-Request-Headers': 'X-Custom'})
    assert response['status'] == '200'
    assert response['access-control-allow-origin'] == 'http://example.com'
    assert response['access-control-allow-methods'] == 'DELETE, GET, PUT'
    assert response['access-control-allow-headers'] == 'ETag, Content-Type, X-Custom'
    assert response['access-control-max-age'] == '600'

def test_not_simple_auth():
    config['cors.allow_creds'] = True
    response, content = http.request('http://0.0.0.0:8080/bags/franny',
            method = 'OPTIONS',
            headers = {'Origin': 'http://example.com',
                'Access-Control-Request-Method': 'DELETE',
                'Access-Control-Request-Headers': 'X-Custom'})
    assert response['status'] == '200'
    assert response['access-control-allow-origin'] == 'http://example.com'
    assert response['access-control-allow-methods'] == 'DELETE, GET, PUT'
    assert response['access-control-allow-headers'] == 'ETag, Content-Type, X-Custom'
    assert response['access-control-max-age'] == '600'
    assert response['access-control-allow-credentials'] == 'true'
    config['cors.allow_creds'] = False

def test_not_simple_400():
    response, content = http.request('http://0.0.0.0:8080/rags',
            method = 'OPTIONS',
            headers = {'Origin': 'http://example.com',
                'Access-Control-Request-Method': 'DELETE',
                'Access-Control-Request-Headers': 'X-Custom'})
    assert response['status'] == '404'

def test_cache_handling():
    bag = Bag('thing')
    store.put(bag)
    tiddler = Tiddler('one', 'thing')
    tiddler.text = '!Hi'
    store.put(tiddler)
    response, content = http.request(
            'http://0.0.0.0:8080/bags/thing/tiddlers/one',
            headers = {'Origin': 'http://example.com'})
    assert response['status'] == '200'
    assert '!Hi' in content
    assert response['access-control-allow-origin'] == '*'
    assert response['access-control-expose-headers'] == 'ETag, Content-Type'
    etag = response['etag']

    response, content = http.request(
            'http://0.0.0.0:8080/bags/thing/tiddlers/one',
            headers = {'Origin': 'http://example.com',
                'If-None-Match': etag})

    assert response['status'] == '304'
    assert response['access-control-allow-origin'] == '*'
    assert response['access-control-expose-headers'] == 'ETag, Content-Type'
