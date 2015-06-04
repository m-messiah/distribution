#!/usr/bin/python
# -*- coding:utf-8 -*-
import re
from glob import glob
import datetime
import dns.name
import dns.message
import dns.query
import json
from os.path import basename
import re
import errno
import requests
import tempfile
import shutil


class Distributor(object):
    def __init__(self, configs_dir):
        self.services = {'web': dict(), 'other': dict()}
        self.changed = []
        self.configs = configs_dir
        self.authors = dict()
        self.re_nginx_server = re.compile(
            '^\s*?server[^#\{\}]*\{[^\}]*?'
            '^\s*?listen\s+([\d\.:]+(?:\s*ssl)?)(?:\s*default)? *?;[^\}]*?'
            '^\s+?(?:server_name|ke_upstream)\s+([^ ][A-Za-z0-9\-_\.: ]+?;(?: # author: (.+?)\n)?)',
            re.DOTALL | re.MULTILINE)
        self.re_nginx_ip = re.compile(
            r'((?:\d{1,3}\.){3}\d{1,3}:?\d*(?:\s*ssl)?)')
        self.re_haproxy = re.compile(
            r'^listen\s+?([\w\d\.:\-_]+)\s+?'
            '(?:(?:\s+?bind\s+?)?'
            '((?:\d{1,3}\.){3}\d{1,3}:\d+)\s+?)+',
            re.DOTALL | re.MULTILINE)
        self.generate()
        self.beautify()

    def generate(self):
        for conf in glob('%s/*' % self.configs):
            if "dns" in conf:
                self.parse_dns(conf)
            elif "nginx" in conf:
                self.parse_nginx(conf)
            elif "haproxy" in conf:
                self.parse_haproxy(conf)
            else:
                print "Parser for %s is not implemented" % conf

    def parse_dns(self, conf):
        servers = [i.split(" ", 1) for i in open(conf).readlines()]
        cat = "DNS_" + basename(conf).replace("dns.", "").replace(".", "_")
        self.services[cat] = dict()
        for server in servers:
            if "_domainkey" in server[0]:
                continue
            (priority, class_path,
             list_type, destination) = server[1].split(" ", 3)

            self.services[cat][server[0]] = {
                "   Priority": [priority],          # For sorting labels
                "  Class": [class_path],
                " Type": [list_type],
                "Dest": [destination.rstrip()]
            }

    def parse_nginx(self, conf):
        servers = [[i[1].strip(), i[0]]
                   for i in self.re_nginx_server.findall(open(conf).read())]
        server_name = basename(conf).replace(".all", "").replace("nginx.", "")

        for server in servers:
            server[0], author = server[0].split(";")
            if "author" in author:
                author = author.split()[-1]
            else:
                author = ""
            listeners = self.re_nginx_ip.findall(server[1])
            ports = filter(
                lambda p: (p != '80') and len(p),
                map(lambda l: l.split(':')[1] if len(l.split(':')) > 1 else '',
                    listeners))
            urls = map(
                lambda l: l + ':' + ",".join(ports) if len(ports) else l,
                map(lambda s: s[1:] if s[0] == '.' else s, server[0].split()))

            def stdports(ipaddr):
                return re.sub(r"\:(80|443 ssl)$", "", ipaddr).replace(" ssl", "")
            listeners = set(map(stdports, listeners))

            for url in urls:
                url = url.lower().decode("idna")
                if url in self.authors:
                    self.authors[url] += " " + author
                else:
                    self.authors[url] = author
                if url in self.services['web'].keys():
                    if server_name in self.services['web'][url].keys():
                        self.services['web'][url][server_name] |= listeners
                    else:
                        self.services['web'][url][server_name] = listeners
                else:
                    self.services['web'][url] = dict()
                    self.services['web'][url][server_name] = listeners

    def parse_haproxy(self, conf):
        listeners = [(i[0].replace("cluster.", ""), i[1])
                     for i in self.re_haproxy.findall(open(conf).read())]

        server_name = basename(conf).replace("haproxy.", "").replace(".all", "")

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
                    self.services[cat][listener[0]][server_name].add(
                        listener[1])
                else:
                    self.services[cat][listener[0]][server_name] = set([
                        listener[1]])
            else:
                self.services[cat][listener[0]] = {
                    server_name: set([listener[1]])}

    def beautify(self):
        for cat in self.services:
            for service in self.services[cat].keys():
                for server_name in self.services[cat][service].keys():
                    if not self.services[cat][service][server_name]:
                        del self.services[cat][service][server_name]
                    else:
                        self.services[cat][service][server_name] = sorted(
                            self.services[cat][service][server_name]
                        )

    def write(self, cat):
        response = [u'<table class="hoverable" id="',
                    u'%s-table">' % cat,
                    u'<thead><tr><th>Services</th>']
        servers = []
        for service in self.services[cat].keys():
            for server_name in self.services[cat][service].keys():
                if re.match("f\dn\d", server_name):
                    servers.append(server_name[:2])
                else:
                    servers.append(server_name)
        servers = list(sorted(set(servers)))
        for server in servers:
            response.append(u"<th>%s</th>" % server)
        if cat == "web":
            response.append(u"<th>Author</th>")
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
            if color > 1 and "DNS" not in cat:
                response.append(u"<tr class=\"red lighten-3\"><th>")
            else:
                response.append(u"<tr><th>")

            clear_service = service
            if " ssl" in clear_service:
                clear_service = "https://" + clear_service.replace(" ssl", "")
            if ":443" in clear_service:
                clear_service = clear_service.replace(":443", "")
            response.append(clear_service)
            if cat == "web":
                try:
                    history = 0
                    if "https://" in clear_service:
                        url = clear_service
                    else:
                        url = "http://" + clear_service
                    r = requests.get("%s/favicon.ico" % url, timeout=2)
                    if r.status_code != 200:
                        response.append(" <i class=\"mdi-action-favorite-outline\"></i>")
                    history += len(r.history)
                    r = requests.get("%s/robots.txt" % url, timeout=2)
                    if r.status_code != 200:
                        response.append(" <i class=\"mdi-action-android\"></i>")
                    elif "text/plain" not in r.headers['content-type']:
                        response.append(" <i class=\"mdi-action-android orange-text\"></i>")
                    history += len(r.history)
                    if len(r.history):
                        response.append(" <i class=\"mdi-navigation-arrow-forward\"></i>")
                    r = requests.head(url, timeout=2)
                    if r.headers.get('x-powered-by'):
                        response.append(" <i class=\"mdi-action-announcement\"></i>")
                except Exception as e:
                    response.append(" <i class=\"mdi-content-clear red-text\"></i>")
            response.append(u"</th>")
            for server in servers:
                if server not in self.services[cat][service].keys():
                    response.append(u"<td> </td>")
                    continue

                response.append(u"<td class=\"text-center\">")
                for ip in self.services[cat][service][server]:
                    response.append(u"%s</br>" % ip)
                response.append(u"</td>")
            if cat == "web":
                author = self.authors.get(service, "").strip()
                if author == "":
                    author = "<i class=\"mdi-social-person-add red-text text-lighten-1\"></i>"
                response.append(u"<td>%s</td>" % author)
            response.append(u"</tr>\n")

        response.append(u"</tbody></table>")
        return u"".join(response)


def get_configs(configs_dir):
    servers = ['server1', 'server2',
               'server3', 'server4',
               ]
    auth = {'PRIVATE-TOKEN': ''}
    url = "https://git.example.com/api/v3/projects"

    for server in servers:
        try:
            id_proj = requests.get("{0}/balancers%2F{1}".format(url, server),
                                   headers=auth).json()[u'id']
        except:
            print "Repository %s does not exists" % server
        else:
            sha = requests.get("%s/%s/repository/commits"
                               % (url, id_proj),
                               headers=auth).json()[0][u'id']
            for filepath in ['usr/local/etc/nginx/nginx.conf',
                             'usr/local/etc/haproxy/haproxy.cfg',
                             'nginx.conf']:
                try:
                    params = {'filepath': filepath}
                    main_file = requests.get("%s/%s/repository/blobs/%s"
                                             % (url, id_proj, sha),
                                             params=params, headers=auth)
                    if main_file.status_code != 200:
                        continue
                    with open("%s/%s.%s.all" % (
                            configs_dir,
                            filepath[filepath.rfind("/")+1:filepath.rfind(".")],
                            server),
                            "w") as config:
                        main_file = main_file.text
                        config.write(main_file)
                        for incl in re.findall(r"(?:^i|^[ \t]+i)nclude (.+);$",
                                               main_file, re.M):
                            try:
                                params = {
                                    'filepath': "%s%s" % (
                                        filepath[:filepath.rfind("/")+1], incl)
                                }
                                include_file = requests.get(
                                    "%s/%s/repository/blobs/%s"
                                    % (url, id_proj, sha),
                                    params=params,
                                    headers=auth
                                ).text
                                config.write(include_file)
                            except:
                                pass
                except:
                    pass

    name_server = "8.8.8.8"  # ns1.example.com
    for domain in ["example.com", ]:
        responses = dns.query.xfr(name_server, dns.name.from_text(domain))
        with open("%s/dns.%s" % (configs_dir, domain), "w") as config:
            for response in responses:
                for line in response.answer:
                    config.write(line.to_text() + "\n")


def create_html():
    temp_dir = tempfile.mkdtemp()
    #print temp_dir
    try:
        get_configs(temp_dir)
        distrib = Distributor(temp_dir)
        for cat in sorted(distrib.services.keys()):
            cat_html = distrib.write(cat).encode("utf8")
            with open("./categories/" + cat + ".html", "w") as w:
                w.write(cat_html)

        with open("./categories/last_sync.html", "w") as last_sync:
            last_sync.write(datetime.datetime.now().strftime("%d %B %H:%M %A"))

    except Exception as e:
        with open("error.log", "w") as error:
            error.write("Exception while creating html: %s\n" % e)
        return
    finally:
        try:
            shutil.rmtree(temp_dir)
        except OSError as exc:
            if exc.errno != errno.ENOENT:  # ENOENT - no such file or directory
                raise

if __name__ == '__main__':
    create_html()

