#!/usr/bin/python
from subprocess import call, check_output
import datetime
import dns.name
import dns.message
import dns.query
import re
import requests


def main():
    servers = ['server1', 'server2',
               'server3', 'server4',
               ]
    auth = {'PRIVATE-TOKEN': ''}
    url = "https://git.example.com/api/v3/projects"
    for server in servers:
        # server_configs - is Group - owner of configs.
        id_proj = requests.get("{0}/server_configs%2F{1}".format(url, server),
                               headers=auth).json()[u'id']
        sha = requests.get("{0}/{1}/repository/commits"
                           .format(url, id_proj),
                            headers=auth).json()[0][u'id']
        for filepath in ['nginx/nginx.conf', 'haproxy/haproxy.cfg']:
            params = {'filepath': filepath}
            mainf = requests.get("{0}/{1}/repository/blobs/{2}"
                                 .format(url, id_proj, sha),
                                 params=params, headers=auth).text
            with open("./configs/{0}.{1}.all"
                      .format(filepath[:filepath.find("/")], server),
                      "w") as config:
                config.write(mainf)
                for incl in re.findall(r"(?:^i|^ +i)nclude (.+);$",
                                       mainf, re.M):
                    params = {
                        'filepath': "{0}/{1}".format(
                            filepath[:filepath.find("/")], incl)
                    }
                    incf = requests.get("{0}/{1}/repository/blobs/{2}"
                                        .format(url, id_proj, sha),
                                                params=params,
                                                headers=auth).text
                    config.write(incf)

    ##############################################
    # This is need, if you has not configs in Git.
    # Syncer can get it directly from server by ssh.
    #
    #for server in servers:
    #    call(["scp", "{0}.example.com:/etc/nginx/nginx.conf".format(server),
    #          "./configs/nginx.{0}.all".format(server)])
    #    config = open("./configs/nginx.{0}.all".format(server), "r").read()
    #
    #    with open("./configs/nginx.{0}.all".format(server), "a") as main:
    #        for incl in re.findall(r"(?:^i|^ +i)nclude (.+);$",
    #                               config, re.M):
    #            main.write("\n{0}".format(
    #                check_output(["ssh", "{0}.example.com".format(server),
    #                              "cat", "/etc/nginx/{0}".format(incl)])
    #            ))
    #
    #    call(["scp",
    #          "{0}.example.com:/etc/haproxy/haproxy.cfg".format(server),
    #          "./configs/haproxy.{0}.all".format(server)])
    ################

    # your dns server with zone_transfer enable
    name_server = "8.8.8.8"  # dns.domain.com
    for domain in ["example.com", "domain.com"]:
        responses = dns.query.xfr(name_server, dns.name.from_text(domain))
        with open("./configs/dns.{0}".format(domain), "w") as config:
            for response in responses:
                for line in response.answer:
                    config.write(line.to_text() + "\n")

    with open("./configs/last_sync.date", "w") as last_sync:
        last_sync.write(datetime.datetime.now().strftime("%d %h %H:%M"))

if __name__ == "__main__":
    main()
