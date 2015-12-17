# coding=utf-8
from unittest import TestCase
from distributor import NginxParser
from os.path import join, dirname, realpath

__author__ = 'm_messiah'


class TestNginxParser(TestCase):
    def setUp(self):
        self.conf = open(
            join(dirname(realpath(__file__)), "nginx.conf")
        ).read()
        self.np = NginxParser()

    def test_parse(self):
        self.servers = self.np.parse(self.conf)
        self.assertIn("http", self.servers)
        self.assertIn("stream", self.servers)
        self.assertIn("log_format", self.servers)

    def test_parse_http(self):
        try:
            _ = len(self.servers)
        except AttributeError:
            self.servers = self.np.parse(self.conf)
        self.assertEqual(3, len(self.servers['http']))
        self.assertListEqual(['example.com', 'example.net', 'example.net'],
                             [s['server_name'][0]
                              for s in self.servers['http']])
        self.assertListEqual(['1.1.1.1:80', '2.2.2.2:80', '2.2.2.2:443 ssl'],
                             [s['listen'][0] for s in self.servers['http']])
        self.assertIn(True, [s['promo'] for s in self.servers['http']])
        self.assertIn("info@example.net",
                      [s['author'] for s in self.servers['http']])

    def test_parse_stream(self):
        try:
            _ = len(self.servers)
        except AttributeError:
            self.servers = self.np.parse(self.conf)

        self.assertEqual(2, len(self.servers['stream']))
        self.assertListEqual(['rdp.example.com', 'git.example.net'],
                             [s['proxy_pass'][0]
                              for s in self.servers['stream']])
        self.assertListEqual(['1.1.1.1:443 ssl', '2.2.2.2:22'],
                             [s['listen'][0] for s in self.servers['stream']])

        self.assertIn("git@example.net",
                      [s['author'] for s in self.servers['stream']])

    def test_parse_log_format(self):
        try:
            _ = len(self.servers)
        except AttributeError:
            self.servers = self.np.parse(self.conf)

        self.assertEqual(2, len(self.servers['log_format']))
        self.assertSetEqual({'spdy_long', 'long'},
                             set(self.servers['log_format'].keys()))
