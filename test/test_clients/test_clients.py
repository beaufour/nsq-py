import mock
import unittest

from nsq import http


class TestClients(unittest.TestCase):
    def setUp(self):
        self.result = mock.Mock()
        self.result.content = '{"foo": "bar"}'
        self.result.status_code = 200
        self.result.reason = 'OK'
        self.func = mock.Mock(return_value=self.result)
        self.client = http.BaseClient('http://foo:1')

        def function(*args, **kwargs):
            return self.func(*args, **kwargs)

        self.function = function

    def test_string(self):
        '''Can make a client with a string'''
        # This test passes if no exception is thrown
        http.BaseClient('http://foo.com:4161')

    def test_tuple(self):
        '''Can create a client with a tuple'''
        http.BaseClient(('foo.com', 4161))

    def test_non_tuple_string(self):
        '''Raises an exception if it's neither a tuple or a string'''
        self.assertRaises(TypeError, http.BaseClient, {})

    def test_no_port(self):
        '''Raises an exception if no port is provided'''
        self.assertRaises(AssertionError, http.BaseClient, 'http://foo.com')

    def test_wrap_basic(self):
        '''Invokes a function with the same args and kwargs'''
        args = [1, 2, 3]
        kwargs = {'whiz': 'bang'}
        http.wrap(self.function)(*args, **kwargs)
        self.func.assert_called_with(*args, **kwargs)

    def test_wrap_non_200(self):
        '''Raises a client exception'''
        self.result.status_code = 500
        self.result.reason = 'Internal Server Error'
        self.assertRaisesRegexp(http.ClientException,
            'Internal Server Error', http.wrap(self.function))

    def test_wrap_exception(self):
        '''Wraps exceptions as ClientExceptions'''
        self.func.side_effect = TypeError
        self.assertRaises(http.ClientException, http.wrap(self.function))

    def test_json_wrap_basic(self):
        '''Returns JSON-parsed content'''
        self.result.content = '{"data":"bar"}'
        self.assertEqual(http.json_wrap(self.function)(), 'bar')

    def test_json_wrap_exception(self):
        '''Raises a generalized exception for failed 200s'''
        # This is not JSON
        self.result.content = '{"'
        self.assertRaises(http.ClientException,
            http.json_wrap(self.function))

    def test_ok_check(self):
        '''Passes through the OK response'''
        self.result.content = 'OK'
        self.assertEqual('OK', http.ok_check(self.function)())

    def test_ok_check_raises_exception(self):
        '''Raises an exception if the respons is not OK'''
        self.result.content = 'NOT OK'
        self.assertRaisesRegexp(
            http.ClientException, 'NOT OK', http.ok_check(self.function))

    def test_get(self):
        '''Gets from the appropriate host with all the provided params'''
        with mock.patch('nsq.http.requests') as MockClass:
            args = [1, 2, 3]
            kwargs = {'whiz': 'bang'}
            MockClass.get.return_value = mock.Mock(
                status_code=200, content='{"foo": "bar"}')
            self.client.get('/path', *args, **kwargs)
            MockClass.get.assert_called_with(
                'http://foo:1/path', *args, **kwargs)

    def test_post(self):
        '''Posts to the appropriate host with all the provided params'''
        with mock.patch('nsq.http.requests') as MockClass:
            args = [1, 2, 3]
            kwargs = {'whiz': 'bang'}
            MockClass.post.return_value = mock.Mock(
                status_code=200, content='{"foo": "bar"}')
            self.client.post('/path', *args, **kwargs)
            MockClass.post.assert_called_with(
                'http://foo:1/path', *args, **kwargs)
