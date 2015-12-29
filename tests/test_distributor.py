from os.path import join, dirname, realpath
from unittest import TestCase

from distributor import Distributor

__author__ = 'm_messiah'


class TestDistributor(TestCase):
    def setUp(self):
        self.pwd = dirname(realpath(__file__))
        self.D = Distributor(self.pwd, join(self.pwd, "config_t.ini"))

    def test_config(self):
        with self.assertRaises(SystemExit):
            Distributor(self.pwd, join(self.pwd, "config_t_bad.ini"))


    def test_parse_nginx(self):
        self.D.parse_nginx(join(self.pwd, "configs", "nginx.test_server.all"))
        self.assertSetEqual({'promo', 'stream', 'web'},
                            set(self.D.services.keys()))

        self.assertSetEqual({'example.net', 'example.net:443'},
                            set(self.D.services['web'].keys()))
        self.assertListEqual(
            [{'2.2.2.2'}, {'2.2.2.2:443'}],
            sorted((s['test_server']
                    for _, s in self.D.services['web'].items()),
                   key=lambda k: next(iter(k)))
        )

        self.assertSetEqual({'example.com'},
                            set(self.D.services['promo'].keys()))
        self.assertSetEqual(
            {'1.1.1.1'},
            self.D.services['promo']['example.com']['test_server']
        )

        self.assertSetEqual({'git.example.net', 'rdp.example.com'},
                            set(self.D.services['stream'].keys()))
        self.assertListEqual(
            [{'1.1.1.1:443'}, {'2.2.2.2:22'}],
            sorted((s['test_server']
                    for _, s in self.D.services['stream'].items()),
                   key=lambda k: next(iter(k)))
        )

        self.assertSetEqual({'web'}, set(self.D._api.keys()))
        self.assertSetEqual({'example.com', 'example.net', 'example.net:443'},
                            set(self.D._api['web']['servers'].keys()))
        self.assertSetEqual({'long', 'spdy_long'},
                            set(self.D._api['web']['log_format'].keys()))

    def test_parse_haproxy(self):
        self.D.parse_haproxy(join(self.pwd, "configs",
                                  "haproxy.test_server.all"))
        self.assertSetEqual({'http', 'ssh'}, set(self.D.services.keys()))
        self.assertSetEqual({'https.example.org'},
                            set(self.D.services['http'].keys()))
        self.assertEqual(
            {'3.3.3.3:443'},
            self.D.services['http']['https.example.org']['test_server']
        )

        self.assertSetEqual({'ssh.example.org'},
                            set(self.D.services['ssh'].keys()))
        self.assertEqual(
            {'3.3.3.3:22'},
            self.D.services['ssh']['ssh.example.org']['test_server']
        )

    def test_index(self):
        index = self.D.index()
        self.assertIn("<html", index)
        self.assertNotIn("{%", index)
        self.assertIn("example.com", index)
        self.assertIn("example.net", index)

    def test_get_cats(self):
        self.assertListEqual(sorted(self.D.services.keys()), self.D.get_cats())
