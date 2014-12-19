WebTest for Twisted
===================

Inspired by [WebTest](https://github.com/Pylons/webtest) for WSGI applications,
txwebtest is an attempt to make life easier when testing Twisted web apps.

So far only the most basic functionality has been implemented. It has only been
tested with [Klein](https://github.com/twisted/klein).

```python
from klein import route, resource
from twisted.internet import defer, task
from txwebtest import TestClient

@route('/')
def home(request):
    return 'Hello, world!'

@defer.inlineCallbacks
def test_app():
    client = TestClient(resource())
    resp = yield client.get('/', status=200)
    assert resp.text == 'Hello, world!'

task.react(lambda reactor: test_app(), [])
```
