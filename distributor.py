#!/usr/bin/python
# -*- coding:utf-8 -*-
import re
from subprocess import check_output, CalledProcessError
from glob import glob


class Distributor(object):
    def __init__(self):
        self.services = {'web': dict(), 'other': dict()}
        self.changed = []
        self.re_nginx_server = re.compile(
            r'[^#]? *?server\s*?{\s*?'
            '(.*?listen\s+(?:[\d\.:]+)(?:\s*ssl)? *?;.*?)'
            '(?:server_name|ke_upstream)\s+([^ ][A-Za-z0-9\-_\.: ]+?);',
            re.DOTALL | re.MULTILINE)
        self.re_nginx_ip = re.compile(r'\n[^#]*?listen\s+?'
                                      '((?:\d{1,3}\.){3}\d{1,3}:?\d*)[;\s]')
        self.re_haproxy = re.compile(r'^listen\s+?([\w\d\.:\-_]+)\s+?'
                                     '(?:(?:\s+?bind\s+?)?'
                                     '((?:\d{1,3}\.){3}\d{1,3}:\d+)\s+?)+',
                                     re.DOTALL | re.MULTILINE)
        self.generate()
        self.beautify()

    def generate(self):
        for conf in glob('./configs/*.all'):
            if conf[10:15] == "nginx":
                self.parse_nginx(conf)
            elif conf[10:17] == "haproxy":
                self.parse_haproxy(conf)
            else:
                print "Parser for {0} is not implemented".format(conf)

    def parse_nginx(self, conf):
        servers = [(i[1].strip(), i[0])
                   for i in self.re_nginx_server.findall(open(conf).read())]
        server_name = conf[16:-4]
        for server in servers:
            listeners = self.re_nginx_ip.findall(server[1])
            ports = filter(
                lambda p: (p != '80') and (p != '443') and len(p),
                map(lambda l: l.split(':')[1] if len(l.split(':')) > 1 else '',
                    listeners))
            urls = " ".join(
                sorted(map(
                    lambda l: l + ':' + ",".join(ports) if len(ports) else l,
                    map(lambda s: s[1:] if s[0] == '.' else s,
                        server[0].split()))))
            print urls
            if urls in self.services['web'].keys():
                if server_name in self.services['web'][urls].keys():
                    self.services['web'][urls][server_name].extend(listeners)
                else:
                    self.services['web'][urls][server_name] = listeners
            else:
                self.services['web'][urls] = dict()
                self.services['web'][urls][server_name] = listeners

    def parse_haproxy(self, conf):
        listeners = [(i[0].replace("cluster.", ""), i[1])
                     for i in self.re_haproxy.findall(open(conf).read())]

        server_name = conf[18:-4]
        if re.match("f\dn\d", server_name):
            server_name = server_name[:2]
        for listener in listeners:
            if listener[0] == "stat":
                continue

            fl = True
            for pattern in [":8080", ":443", ":80"]:
                if pattern in listener[1]:
                    cat = "http"
                    fl = False
                    break

            if fl:
                for pattern in [":1433"]:
                    if pattern in listener[1]:
                        cat = "sql"
                        fl = False
                        break

            if fl:
                for pattern in [":25", ":143", ":110"]:
                    if pattern in listener[1]:
                        cat = "mail"
                        fl = False
                        break

            if fl:
                for pattern in ["ssh", "sql", "rdp", "mail",
                                "http", "ldap", "sms"]:
                    if pattern in listener[0]:
                        cat = pattern
                        fl = False
                        break

            if fl:
                cat = "other"

            if cat not in self.services:
                self.services[cat] = dict()
            if listener[0] in self.services[cat]:
                if server_name in self.services[cat][listener[0]].keys():
                    self.services[cat][listener[0]][server_name].append(
                        listener[1])
                else:
                    self.services[cat][listener[0]][server_name] = [
                        listener[1], ]
            else:
                self.services[cat][listener[0]] = {server_name:
                                                   [listener[1], ]
                                                   }

    def beautify(self):
        for cat in self.services:
            for service in self.services[cat].keys():
                for server_name in self.services[cat][service].keys():
                    if not self.services[cat][service][server_name]:
                        del self.services[cat][service][server_name]
                    else:
                        self.services[cat][service][server_name] = sorted(
                            list(set(self.services[cat][service][server_name]))
                        )

    def write(self, cat):
        response = [u"<table><thead><tr><th>Services</th>"]
        servers = []
        for service in self.services[cat].keys():
            for server_name in self.services[cat][service].keys():
                if re.match("f\dn\d", server_name):
                    servers.append(server_name[:2])
                else:
                    servers.append(server_name)
        servers = list(sorted(set(servers)))
        for server in servers:
            response.append(u"<th>{0}</th>".format(server))
        response.append(u"</tr></thead>\n<tbody>")
        services1 = []
        for service in sorted(self.services[cat].keys()):
            color = len(self.services[cat][service].keys())
            services1.append((color, service))
        services = (sorted([(i[1], i[0])
                            for i in services1
                            if i[0] > 1])
                    +
                    sorted([(i[1], i[0])
                            for i in services1 if i[0] < 2]))
        for (service, color) in services:
            if color > 1:
                response.append(u"<tr class=\"error\"><th>")
                try:
                    a = check_output(["host", service.split()[0].lstrip(".")])
                    ip_address = re.search(r"((?:\d{1,3}\.){3}\d{1,3})",
                                           a).group(0)
                except AttributeError:
                    ip_address = "256"
                except CalledProcessError:
                    ip_address = "-1"
            else:
                response.append(u"<tr><th>")
                ip_address = "256"

            response.append(
                u"</br>".join(map(lambda s: s.lower().decode("idna"),
                                  service.split() + [""])))
            response.append(u"</th>")
            for server in servers:
                if server in self.services[cat][service].keys():
                    response.append(u"<td>")
                    for ip in sorted(
                            list(set(self.services[cat][service][server]))):
                        if ip.count(ip_address) > 0:
                            response.append(u"<b>{}</b></br>".format(ip))
                        else:
                            response.append(u"{}</br>".format(ip))
                    response.append(u"</td>")
                else:
                    response.append(u"<td> </td>")
            response.append(u"</tr>\n")

        response.append(u"</tbody></table>")
        return u"".join(response)
