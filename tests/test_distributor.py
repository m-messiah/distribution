from os.path import join, dirname, realpath
from unittest import TestCase

from distributor import Distributor

__author__ = 'm_messiah'


class TestDistributor(TestCase):
    def setUp(self):
        self.pwd = dirname(realpath(__file__))
        self.D = Distributor(join(self.pwd, "configs"),
                             join(self.pwd, "config_t.ini"))

    def test_config(self):
        with self.assertRaises(SystemExit):
            try:
                with self.assertLogs():
                    Distributor(join(self.pwd, "configs"),
                                join(self.pwd, "config_t_bad.ini"))
            except AttributeError:
                Distributor(join(self.pwd, "configs"),
                            join(self.pwd, "config_t_bad.ini"))

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

    def test_write_nginx(self):
        self.D.parse_nginx(join(self.pwd, "configs", "nginx.test_server.all"))
        self.D.parse_nginx(join(self.pwd, "configs", "nginx.front1.all"))
        web_table = self.D.write("web")

        self.assertIn("ch-test_server", web_table)
        self.assertIn("ch-author", web_table)
        self.assertIn("th:nth-child", web_table)
        self.assertIn("<table", web_table)
        self.assertIn("</table>", web_table)
        self.assertIn("<th>front</th>", web_table)
        self.assertIn('class="zone', web_table)
        self.assertIn('id="web-table"', web_table)
        self.assertIn('https://example.net', web_table)

        promo_table = self.D.write("promo")
        self.assertIn("<table", promo_table)
        self.assertIn("</table>", promo_table)
        self.assertNotIn('class="zone', promo_table)
        self.assertIn('id="promo-table"', promo_table)
        self.assertIn('example.com', promo_table)

        stream_table = self.D.write("stream")
        self.assertIn("<table", stream_table)
        self.assertIn("</table>", stream_table)
        self.assertIn('class="zone', stream_table)
        self.assertIn('id="stream-table"', stream_table)
        self.assertIn('rdp.example.com', stream_table)
        self.assertIn('git.example.net', stream_table)

    def test_write_haproxy(self):
        self.D.parse_haproxy(
            join(self.pwd, "configs", "haproxy.test_server.all")
        )
        http_table = self.D.write("http")
        self.assertIn("<table", http_table)
        self.assertIn("</table>", http_table)
        self.assertIn('class="zone', http_table)
        self.assertIn('id="http-table"', http_table)
        self.assertIn('https.example.org', http_table)

        ssh_table = self.D.write("ssh")
        self.assertIn("<table", ssh_table)
        self.assertIn("</table>", ssh_table)
        self.assertIn('class="zone', ssh_table)
        self.assertIn('id="ssh-table"', ssh_table)
        self.assertIn('ssh.example.org', ssh_table)
