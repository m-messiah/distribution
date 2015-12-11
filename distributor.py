#!/usr/bin/env python
# -*- coding:utf-8 -*-
import string
from pyparsing import (Literal, White, Word, alphanums, CharsNotIn,
                       Optional, Forward, Group, ZeroOrMore, OneOrMore,
                       QuotedString, restOfLine)

try:
    import urllib3.contrib.pyopenssl
    urllib3.contrib.pyopenssl.inject_into_urllib3()
except:
    pass
import datetime
from dns import query, name as dns_name
import dns.message
import dns.resolver
import dns.rdatatype
import dns.tsig
import dns.tsigkeyring
import errno
import requests
import tempfile
import shutil
from os import listdir
from os.path import basename, splitext, dirname, join as pjoin
from re import match, compile, DOTALL, MULTILINE, findall, M as REM
import json
from collections import defaultdict

try:
    import credentials
except ImportError:
    print "No credentials file. Sync is unavailable"

ICON = (" <i title=\"%(hint)s\" "
        "class=\"tiny material-icons %(color)s\">%(icon)s</i>")

NO_ROBOTS = ICON % {"color": "", "icon": "android",
                    "hint": "no robots.txt"}
BAD_ROBOTS = ICON % {'color': "orange-text", 'icon': "android",
                     'hint': "bad robots.txt"}
NO_FAVICON = ICON % {"color": "", "icon": "favorite_border",
                     "hint": "no favicon.ico"}
BAD_FAVICON = ICON % {"color": "orange-text", "icon": "favorite_border",
                      "hint": "favicon not ico"}
ANONYMOUS = ICON % {"color": "red-text text-lighten-1", "icon": "person_add",
                    "hint": "no author"}
REDIRECT = ICON % {"color": "", "icon": "arrow_forward",
                   "hint": "redirect detected"}
BAD_HEADER = ICON % {"color": "", "icon": "announcement",
                     "hint": "X-Powered-by header"}
NO_URL = ICON % {"color": "red-text", "icon": "clear",
                 "hint": "%s"}
DELEGATE = ICON % {"color": "green-text", "icon": "done",
                   "hint": u"Делегирован"}
DOTTED = ICON % {"color": "orange-text", "icon": "filter_center_focus",
                 "hint": ".domain"}
INSECURE = ICON % {"color": "red-text text-lighten-1", "icon": "security",
                   "hint": "bad ssl"}
NO_SITEMAP = ICON % {"color": "", "icon": "dashboard",
                     "hint": "no sitemap"}
BAD_SITEMAP = ICON % {"color": "orange-text", "icon": "dashboard",
                      "hint": "sitemap not xml"}
DOUBLE_HEADER = ICON % {"color": "", "icon": "filter_2",
                        "hint": "duplicate header with different info"}
DOUBLE_HEADER_SAME = ICON % {"color": "orange-text", "icon": "filter_2",
                             "hint": "duplicate header with same info"}

NO_H1 = "&lt;h1&gt;"
NO_TITLE = "&lt;title&gt;"
NO_DESCRIPTION = "&lt;descr&gt;"


class NginxParser(object):
    def __init__(self):
        left_bracket = Literal("{").suppress()
        right_bracket = Literal("}").suppress()
        semicolon = Literal(";").suppress()
        space = White().suppress()
        key = Word(alphanums + "+.-_/")
        value = ZeroOrMore(
            CharsNotIn('{};#"\'') | space |
            QuotedString("'", escChar='\\', multiline=True) |
            QuotedString('"', escChar='\\', multiline=True))
        # modifier for location uri [ = | ~ | ~* | ^~ ]
        modifier = Literal("=") | Literal("~*") | Literal("~") | Literal("^~")

        comment = Literal('#').suppress() + Optional(restOfLine)

        # rules
        assignment = Group(
            (key | value) + value + semicolon +
            Optional(space + comment))
        block = Forward()

        block << Group(
            Group(key + Optional(space + modifier) + Optional(space) +
                  Optional(value) + Optional(space + value)) +
            left_bracket +
            Group(ZeroOrMore(assignment | block | comment.suppress())) +
            right_bracket)

        def commentHandler(t):
            result = []

            if "promo" in t[0]:
                result.append("promo")
            if "author: " in t[0]:
                try:
                    email = t[0].split("author: ")[1].strip()
                    result.append(email)
                except Exception as e:
                    result.append(t[0])
            return result

        comment.setParseAction(commentHandler)

        self.script = OneOrMore(assignment | block | comment.suppress())

    def parse(self, s):
        def toDict(o):
            d = defaultdict(list)
            for i in o:
                try:
                    d[i[0] if isinstance(i[0], (str, int))
                      else " ".join(i[0])].append(
                        i[1] if isinstance(i[1], (str, int)) else toDict(i[1]))
                except:
                    continue
                if 'promo' in i:
                    d['promo'] = True
                if '@' in i[-1] and "@go" not in i[-1]:
                    d['author'] = i[-1]
            return d

        servers = {'http': [], 'stream': [], 'log_format': {}}
        for t in self.script.parseString(s).asList():
            if len(t) and t[0] in [['http'], ['stream']]:
                for tt in t[1]:
                    if tt[0] == ["server"]:
                        servers[t[0][0]].append(toDict(tt[1]))
                    if tt[0] == 'log_format':
                        servers[tt[0]][tt[1].strip()] = tt[2].strip()

        return servers


# noinspection PySetFunctionToLiteral
class Distributor(object):
    def __init__(self, configs_dir):
        self.services = defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(set)))
        self.api = dict()
        self.changed = []
        self.configs = configs_dir
        self.authors = defaultdict(set)
        self.re_haproxy = compile(
            r'^listen\s+?([\w\d\.:\-_]+)\s+?'
            '(?:(?:\s+?bind\s+?)?'
            '((?:\d{1,3}\.){3}\d{1,3}:\d+)\s+?)+',
            DOTALL | MULTILINE)
        self.generate()
        self.beautify()

    def generate(self):
        for conf in listdir(self.configs):
            if "dns" in conf:
                self.parse_dns(conf)
            elif "nic" in conf:
                self.parse_nic(conf)
            elif "nginx" in conf:
                self.parse_nginx(conf)
            elif "haproxy" in conf:
                self.parse_haproxy(conf)
            else:
                print "Parser for %s is not implemented" % conf

    def parse_dns(self, conf):
        servers = [i.split(" ", 1) for i in open(conf).readlines()]
        cat = "DNS_" + basename(conf).replace("dns.", "").replace(".", "_")
        for server in servers:
            if "_domainkey" in server[0]:
                continue
            (priority, class_path,
             list_type, destination) = server[1].split(" ", 3)

            self.services[cat][server[0]] = {
                "   Priority": [priority],  # For sorting labels
                "  Class": [class_path],
                " Type": [list_type],
                "Dest": [destination.rstrip()]
            }

    def parse_nic(self, conf):
        domains = json.load(open(conf))
        for domain in domains:
            self.services["NIC"][domain['domain']] = {
                "    Status": [domain['status']],
                "   TXT": domain['txt'],
                "  NS": domain['ns'].items(),
                " Till": [domain['till']],
                "Auto-renew": [domain['sost']],
            }

    def parse_nginx(self, conf):
        servers = NginxParser().parse(open(conf).read())
        server_name = basename(conf).replace(".all", "").replace("nginx.", "")

        if 'web' not in self.api:
            self.api['web'] = {'servers': {}, 'log_format': {}}

        self.api['web']['log_format'].update(servers['log_format'])

        # Parse http section
        for server in servers["http"]:
            if "location / " not in server:
                continue
            cat = "promo" if "promo" in server and server['promo'] else "web"
            if "author" in server and server['author']:
                author = server['author']
            else:
                author = ""
            try:
                log = server['access_log'][0].split()
            except (IndexError, ValueError, TypeError):
                log = ["", ""]
            if len(log) > 1:
                log_path, log_format = map(lambda i: i.strip(), log[:2])
            else:
                log_path, log_format = log[0], ""
            listeners = server['listen']
            ports = filter(
                lambda p: (p != '80') and len(p),
                map(lambda l: l.split()[0].split(':')[1]
                    if len(l.split()[0].split(':')) > 1 else '',
                    listeners))
            if server['server_name'] and '_' not in server['server_name'][0]:
                urls = map(
                    lambda l: l + ':' + ",".join(ports) if len(ports) else l,
                    server['server_name'][0].split())
            else:
                continue

            def std_ports(ip_addr):
                ip_addr = ip_addr.split()[0]
                if ":80" == ip_addr[-3:]:
                    return ip_addr[:-3]
                return ip_addr

            listeners = set(map(std_ports, listeners))

            for url in urls:
                url = url.lower().decode("idna")
                self.authors[url].add(author)
                self.services[cat][url][server_name].update(listeners)

                self.api['web']['servers'][url] = {
                    'author': author,
                    'log': log_path,
                    'log_format': log_format
                }

        # Parse Stream section
        for server in servers["stream"]:
            cat = "stream"
            if "author" in server and server['author']:
                author = server['author']
            else:
                author = ""
            listeners = set(map(lambda l: l.split()[0], server['listen']))
            url = server['proxy_pass'][0]
            self.authors[url].add(author)
            self.services[cat][url][server_name].update(listeners)

    def parse_haproxy(self, conf):
        listeners = [(i[0].replace("cluster.", ""), i[1])
                     for i in self.re_haproxy.findall(open(conf).read())]

        server = basename(conf).replace("haproxy.", "").replace(".all", "")

        for listener in listeners:
            if listener[0] == "stat":
                continue

            fl = True
            cat = "other"
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

            self.services[cat][listener[0]][server].add(listener[1])

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
        response = [
            u'<table class="hoverable" id="%s-table">' % cat,
            u'<thead><tr><th>Services</th>']

        try:
            response = open("./templates/%s.html" % cat,
                            "r").readlines() + response
        except IOError:
            pass

        servers = set()
        for service in self.services[cat].keys():
            for server_name in self.services[cat][service].keys():
                servers.add(server_name)
        servers = sorted(servers)
        for server in servers:
            response.append(u"<th>%s</th>" % server)
        if cat == "web" or cat == "promo" or cat == "stream":
            response.append(u"<th>Author</th>")
        response.append(u"</tr></thead>\n<tbody>")
        services1 = {0: [], 1: []}
        for service in self.services[cat].keys():
            color = len(self.services[cat][service].keys())
            services1[1 if color > 1 else 0].append((color, service))

        def skip_www(cs):
            # Use for sorting
            s = cs[0]
            if len(s) > 4 and "www." in s[:4]:
                return s[4:] + " "
            else:
                return s

        services = (
            sorted([(i[1], i[0]) for i in services1[1]], key=skip_www) +
            sorted([(i[1], i[0]) for i in services1[0]], key=skip_www)
        )
        for (service, color) in services:
            errors = False
            if color > 1 and "DNS" not in cat and "NIC" not in cat:
                response.append(u"<tr class=\"red lighten-3\"><th>")
            else:
                server = self.services[cat][service].keys()[0]
                response.append(u"<tr class=\"zone%s\"><th> "
                                % servers.index(server))

            clear_service = service
            dotted = False
            if clear_service[0] == ".":
                clear_service = clear_service[1:]
                dotted = True
            if ":443" in clear_service:
                clear_service = "https://" + clear_service.replace(":443", "")
            response.append(clear_service)
            response.append(DOTTED if dotted else "")
            if cat == "web" or cat == "promo":
                history = 0
                if "https://" in clear_service:
                    url = clear_service
                else:
                    url = "http://" + clear_service
                url = url.split(",")[0]
                try:
                    if cat == "promo":
                        r = requests.get("%s/favicon.ico" % url, timeout=5)
                        if r.status_code != 200:
                            response.append(NO_FAVICON)
                        elif "image/x-icon" not in r.headers['content-type']:
                            response.append(BAD_FAVICON)
                        history += len(r.history)
                        r = requests.get("%s/robots.txt" % url, timeout=5)
                        if r.status_code != 200:
                            response.append(NO_ROBOTS)
                        elif "text/plain" not in r.headers['content-type']:
                            response.append(BAD_ROBOTS)
                        history += len(r.history)
                        r = requests.get("%s/sitemap.xml" % url, timeout=5)
                        if r.status_code != 200:
                            response.append(NO_SITEMAP)
                        elif "text/xml" not in r.headers['content-type']:
                            response.append(BAD_SITEMAP)
                        r = requests.get(url, timeout=5)
                        history += len(r.history)
                        if len(r.history):
                            response.append(REDIRECT)
                        if r.headers.get('x-powered-by'):
                            response.append(BAD_HEADER)
                        for head_name, header in r.headers.items():
                            if "set-cookie" in head_name:
                                continue
                            h = map(lambda s: s.strip(), header.split(","))
                            if len(h) > len(set(h)):
                                response.append(DOUBLE_HEADER_SAME)
                                break

                        if "<h1" not in r.text:
                            response.append(NO_H1)
                        if "<title" not in r.text:
                            response.append(NO_TITLE)
                        if 'name="description"' not in r.text:
                            response.append(NO_DESCRIPTION)

                    else:
                        r = requests.get(url, timeout=5)
                        history += len(r.history)
                        if len(r.history):
                            response.append(REDIRECT)
                        if r.headers.get('x-powered-by'):
                            response.append(BAD_HEADER)
                        for head_name, header in r.headers.items():
                            if "set-cookie" in head_name:
                                continue
                            h = map(lambda s: s.strip(), header.split(","))
                            if len(h) > len(set(h)):
                                response.append(DOUBLE_HEADER_SAME)
                                break

                except requests.exceptions.SSLError:
                    response.append(INSECURE)
                except Exception as e:
                    response.append(NO_URL % e)
            response.append(u"</th>")
            for server in servers:
                if server not in self.services[cat][service].keys():
                    if "NIC" in cat and "NS" in server:
                        errors |= True
                    response.append(u"<td> </td>")
                    continue

                if "NIC" in cat and "Status" in server:
                    response.append(
                        u"<td class=\"text-center hide-on-small-only\">")
                else:
                    response.append(u"<td class=\"text-center\">")

                if "NIC" in cat and "NS" in server:
                    for ip, stat in self.services[cat][service][server]:
                        response.append(u"%s %s</br>" %
                                        (ip, DELEGATE if stat else NO_URL))
                        if not stat:
                            errors |= True
                elif "TXT" not in server:
                    for ip in self.services[cat][service][server]:
                        response.append(u"%s</br>" % ip)
                if "NIC" in cat and "TXT" in server:
                    if u"Не делегирован" not in u"".join(
                            self.services[cat][service]["    Status"]):
                        spf, dmarc = self.services[cat][service][server]
                        response.append("spf ")
                        if spf < 1:
                            response.append(DELEGATE)
                        elif spf > 1:
                            response.append(INSECURE)
                            errors |= True
                        else:
                            response.append(NO_URL)
                            errors |= True

                        response.append("<br>dmarc ")
                        if dmarc < 1:
                            response.append(DELEGATE)
                        else:
                            response.append(NO_URL)
                            errors |= True

                response.append(u"</td>")
                if "NIC" in cat and "Status" in server:
                    status = u"".join(self.services[cat][service][server])
                    if u"Не делегирован" in status:
                        response.append(
                            u"<td class=\"hide-on-med-and-up\">%s</td>"
                            % NO_URL)
                    else:
                        response.append(
                            u"<td class=\"hide-on-med-and-up\">%s</td>"
                            % DELEGATE)
            if cat == "web" or cat == "promo" or cat == "stream":
                author = " ".join(filter(len, self.authors.get(service, {})))
                if author == "":
                    author = ANONYMOUS
                response.append(u"<td>%s</td>" % author)
            response.append(u"<td class=\"hide\">%s</td>"
                            % (1 if errors else 0))
            response.append(u"</tr>\n")

        response.append(u"</tbody></table>")
        return u"".join(response)


def get_configs(configs_dir):
    servers = ['server1', 'server2',
               'server3', 'server4']
    auth = {'PRIVATE-TOKEN': credentials.GIT_TOKEN}
    url = "https://gitlab.com/api/v3/projects"

    for server in servers:
        try:
            id_proj = requests.get("{0}/fronts%2F{1}".format(url, server),
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
                    with open(
                            pjoin(configs_dir, "%s.%s.all"
                                  % (splitext(basename(filepath))[0], server)),
                            "w") as config:
                        main_file = main_file.text

                        for incl in findall(
                                r"(?:^i|^[ \t]+i)nclude (.+);$",
                                main_file, REM):
                            try:
                                params = {
                                    'filepath': pjoin(dirname(filepath), incl)
                                }
                                include_file = requests.get(
                                    "%s/%s/repository/blobs/%s"
                                    % (url, id_proj, sha),
                                    params=params,
                                    headers=auth
                                )
                                if include_file.status_code == 200:
                                    main_file = main_file.replace(
                                        "include " + incl + ";",
                                        include_file.text)
                            except:
                                pass
                        config.write(main_file)
                except:
                    pass

    name_server = "ns.example.com"
    keyring = dns.tsigkeyring.from_text(
        {credentials.TSIG_NAME: credentials.TSIG_KEY}
    )
    for domain in ["example.com", "example.net"]:
        try:
            responses = query.xfr(name_server, dns_name.from_text(domain),
                                  keyring=keyring,
                                  keyname=credentials.TSIG_NAME,
                                  keyalgorithm=dns.tsig.HMAC_SHA512)
            with open("%s/dns.%s" % (configs_dir, domain), "w") as config:
                for response in responses:
                    for line in response.answer:
                        config.write(line.to_text() + "\n")
        except:
            pass

    # NIC.ru
    s = requests.Session()
    login = s.post("https://www.nic.ru/login/manager/",
                   data={'login': credentials.NIC_LOGIN,
                         'client_type': 'NIC-D',
                         'password': credentials.NIC_PASSWORD,
                         'password_type': 'adm'})
    if login.status_code == 200:
        csv = s.get("https://www.nic.ru/manager/my_domains.cgi"
                    "?step=srv.my_domains&view.format=csv",
                    verify=False)
        if csv.status_code == 200:
            csv = csv.text.encode("utf8")

            def check_dns(domain, ns):
                ns_s = filter(len, map(lambda s: s.strip(),
                                       ns.replace('"', '').split(';')))
                if len(ns_s) < 1:
                    return {}
                mess = dns.message.make_query(dns_name.from_text(domain),
                                              dns.rdatatype.SOA)
                result = {}
                for ns in ns_s:
                    try:
                        name_s = dns_name.from_text(ns.split()[0]).to_text()
                        answer = query.tcp(mess, name_s, timeout=2)
                        if len(answer.authority):
                            result[ns] = True
                        else:
                            rr = answer.answer[0][0]
                            if rr.rdtype == dns.rdatatype.SOA:
                                result[ns] = True
                            else:
                                result[ns] = False
                    except:
                        result[ns] = False
                return result

            def check_txt(domain, status):
                spf, dmarc = 1, 1
                if u"Не делегирован" in status.decode("utf8"):
                    return spf, dmarc
                try:
                    mess = dns.resolver.query(dns_name.from_text(domain),
                                              dns.rdatatype.TXT)
                except:
                    spf = 1
                else:
                    txts = [txt for rdata in mess for txt in rdata.strings]

                    spfs = filter(lambda i: "v=spf1" in i, txts)
                    if not spfs:
                        spf = 1
                    else:
                        if "+all" in " ".join(spfs):
                            spf = 2
                        else:
                            spf = 0
                try:
                    mess = dns.resolver.query(
                        dns_name.from_text("_dmarc." + domain),
                        dns.rdatatype.TXT)
                except:
                    return spf, dmarc
                else:
                    txts = [txt for rdata in mess for txt in rdata.strings]

                    if filter(lambda i: "v=DMARC1" in i, txts):
                        dmarc = 0
                    else:
                        dmarc = 1
                    return spf, dmarc

            def get_dns_info(info):
                return {
                    'domain': info[0],
                    'ns': check_dns(info[1], info[2]),
                    'txt': check_txt(info[1], info[5]),
                    'status': info[5],
                    'sost': info[6],
                    'till': info[7]
                }

            csv = map(lambda l: get_dns_info(l.split(",")),
                      filter(len, csv.split("\n")[2:]))
            with open("%s/nic" % configs_dir, "w") as config:
                config.write(json.dumps(csv))


def create_html():
    temp_dir = tempfile.mkdtemp()
    try:
        get_configs(temp_dir)
        distrib = Distributor(temp_dir)
        for cat in sorted(distrib.services.keys()):
            cat_html = distrib.write(cat).encode("utf8")
            with open("./categories/" + cat + ".html", "w") as w:
                w.write(cat_html)

        json.dump(distrib.api, open("./categories/api.json", "w"))

        with open("./categories/last_sync.html", "w") as last_sync:
            last_sync.write(datetime.datetime.now().strftime("%d %B %H:%M %A"))

    except Exception as e:
        with open("error.log", "w") as error:
            error.write("%s\tException while creating html: %s\n" % (
                datetime.datetime.now().strftime("%d %B %H:%M %A"), e))
        return
    finally:
        try:
            # print temp_dir
            shutil.rmtree(temp_dir)
        except OSError as exc:
            if exc.errno != errno.ENOENT:  # ENOENT - no such file or directory
                raise


if __name__ == '__main__':
    create_html()
