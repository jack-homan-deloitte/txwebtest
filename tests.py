from klein import Klein
from twisted.internet import defer
from twisted.trial.unittest import TestCase
from txwebtest import TestClient, TestRequest

from txwebtest._compat import parse_qs


class Tests(TestCase):
    def setUp(self):
        self.app = TestClient(create_app().resource())

    @defer.inlineCallbacks
    def test_status_check(self):
        yield self.app.get('/names/4', status=404)
        try:
            yield self.app.get('/names/5', status=200)
            self.fail()
        except AssertionError:
            pass

    @defer.inlineCallbacks
    def test_post_with_body(self):
        resp = yield self.app.post('/names', 'name=Ann', status=201)
        new_item_path = resp.get_header('Location')
        resp = yield self.app.get(new_item_path, status=200)
        assert resp.text == 'Ann', "{resp.text} != Ann".format(resp=resp)

    @defer.inlineCallbacks
    def test_put_with_body(self):
        yield self.app.put('/names/4', 'name=Ann', status=200)
        resp = yield self.app.get('/names/4', status=200)
        assert resp.text == 'Ann'

    @defer.inlineCallbacks
    def test_delete(self):
        yield self.app.put('/names/4', 'name=Ann', status=200)
        yield self.app.delete('/names/4', status=200)
        yield self.app.get('/names/4', status=404)

    @defer.inlineCallbacks
    def test_sentLength(self):
        yield self.app.put('/names/4', 'name=Ann', status=200)
        request = TestRequest(path="/names/4", method="GET")
        resp = yield self.app.request(request)
        assert request.sentLength == len("Ann")


def create_app():
    ''' A simple Klein app that associates ints with names. '''

    app = Klein()
    results = {}

    @app.route('/names', methods=['POST'])
    def post(request):
        name = request.args['name'][0]
        item_id = max(results.keys()) + 1 if results else 1
        results[item_id] = name
        request.setHeader('Location', '/names/%s' % item_id)
        request.setResponseCode(201)
        return name

    @app.route('/names/<int:item_id>', methods=['GET'])
    def get(request, item_id):
        try:
            return results[item_id]
        except KeyError:
            request.setResponseCode(404)

    @app.route('/names/<int:item_id>', methods=['PUT'])
    def put(request, item_id):
        data = request.content.read()
        args = parse_qs(data)
        name = args['name'][0]
        results[item_id] = name
        return ''

    @app.route('/names/<int:item_id>', methods=['DELETE'])
    def delete(request, item_id):
        results.pop(item_id, None)

    return app
