import unittest

import uuid

from nsq.clients import nsqd, ClientException
from nsq.util import pack
from common import IntegrationTest, ClientTest


class TestNsqdClient(ClientTest):
    '''Testing the nsqd client in isolation'''
    def setUp(self):
        self.client = nsqd.Client('http://foo:1')

    def test_mpub_ascii(self):
        '''Publishes ascii messages fine'''
        with self.patched_post() as post:
            post.return_value.content = 'OK'
            messages = map(str, range(10))
            self.client.mpub('topic', messages, binary=False)
            post.assert_called_with(
                '/mpub', params={'topic': 'topic'}, data='\n'.join(messages))

    def test_mpub_binary(self):
        '''Publishes messages with binary fine'''
        with self.patched_post() as post:
            post.return_value.content = 'OK'
            messages = map(str, range(10))
            self.client.mpub('topic', messages)
            post.assert_called_with(
                '/mpub',
                params={'topic': 'topic', 'binary': True},
                data=pack(messages)[4:])

    def test_mpub_ascii_exception(self):
        '''Raises an exception when ascii-mpub-ing messages with newline'''
        messages = ['hello\n', 'how\n', 'are\n', 'you\n']
        self.assertRaises(
            ClientException, self.client.mpub, 'topic', messages, binary=False)


class TestNsqdClientIntegration(IntegrationTest):
    '''An integration test of the nsqd client'''
    def test_ping_ok(self):
        '''Make sure ping works in a basic way'''
        self.assertEqual(self.nsqd.ping(), 'OK')

    def test_info(self):
        '''Info works in a basic way'''
        self.assertIn('version', self.nsqd.info()['data'])

    def test_pub(self):
        '''Publishing a message works as expected'''
        self.assertEqual(self.nsqd.pub(self.topic, 'message'), 'OK')
        topic = self.nsqd.clean_stats()['data']['topics'][self.topic]
        self.assertEqual(topic['channels'][self.channel]['depth'], 1)

    def test_mpub_ascii(self):
        '''Publishing messages in ascii works as expected'''
        messages = map(str, range(100))
        self.assertTrue(self.nsqd.mpub(self.topic, messages, binary=False))

    def test_mpub_binary(self):
        '''Publishing messages in binary works as expected'''
        messages = map(str, range(100))
        self.assertTrue(self.nsqd.mpub(self.topic, messages))

    def test_create_topic(self):
        '''Topic creation should work'''
        topic = uuid.uuid4().hex
        with self.delete_topic(topic):
            # Ensure the topic doesn't exist beforehand
            self.assertNotIn(topic, self.nsqd.clean_stats()['data']['topics'])
            self.assertTrue(self.nsqd.create_topic(topic))
            # And now it exists afterwards
            self.assertIn(topic, self.nsqd.clean_stats()['data']['topics'])

    # def test_empty_topic(self):
    #     '''We can drain a topic'''
    #     self.nsqd.pub(self.topic, 'foo')
    #     self.nsqd.empty_topic(self.topic)
    #     topic = self.nsqd.clean_stats()['data']['topics'][self.topic]
    #     self.assertEqual(topic['channels'][self.channel]['depth'], 0)

    def test_delete_topic(self):
        '''We can delete a topic'''
        topic = uuid.uuid4().hex
        with self.delete_topic(topic):
            self.nsqd.create_topic(topic)
            self.assertTrue(self.nsqd.delete_topic(topic))
            # Ensure the topic doesn't exist afterwards
            self.assertNotIn(topic, self.nsqd.clean_stats()['data']['topics'])

    def test_pause_topic(self):
        '''We can pause a topic'''
        self.assertTrue(self.nsqd.pause_topic(self.topic))

    def test_unpause_topic(self):
        '''We can unpause a topic'''
        self.nsqd.pause_topic(self.topic)
        self.assertTrue(self.nsqd.unpause_topic(self.topic))

    def test_create_channel(self):
        '''We can create a channel'''
        # This is pending, related to an issue:
        #   https://github.com/bitly/nsq/issues/313
        # self.nsqd.create_channel(self.topic, self.channel)
        # self.assertEqual(self.nsqd.stats(), {})

    def test_clean_stats(self):
        '''Clean stats turns 'topics' and 'channels' into dictionaries'''
        stats = self.nsqd.clean_stats()
        self.assertIsInstance(stats['data']['topics'], dict)
        self.assertIsInstance(
            stats['data']['topics'][self.topic]['channels'], dict)

if __name__ == '__main__':
    unittest.main()
