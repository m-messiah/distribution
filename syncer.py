#!/usr/bin/python
from subprocess import call, check_output
import re
import requests
import json


def main():
    servers = ['server1', 'server2',
               'server3', 'server4',
               ]
    auth = {'PRIVATE-TOKEN': ''}
    url = "https://git.example.com/api/v3/projects"
    r = requests.get(url, headers=auth)
    projects = r.json()
    for project in projects:
        if project[u'name'] in servers:
            server = project[u'name']
            id_proj = project[u'id']
            r = requests.get("{0}/{1}/repository/commits"
                             .format(url, id_proj), headers=auth)
            sha = r.json()[0][u'id']
            for filepath in ['nginx/nginx.conf', 'haproxy/haproxy.cfg']:
                params = {'filepath': filepath}
                r = requests.get("{0}/{1}/repository/blobs/{2}"
                                 .format(url, id_proj, sha),
                                 params=params, headers=auth)
                with open("./configs/{0}.{1}.all"
                          .format(filepath[:filepath.find("/")], server),
                          "w") as config:
                    config.write(r.text)

    #for server in servers:
        #call(["scp", "{0}.example.com:/etc/nginx/nginx.conf".format(server),
        #      "./configs/nginx.{0}.all".format(server)])
        #config = open("./configs/nginx.{0}.all".format(server), "r").read()

        #with open("./configs/nginx.{0}.all".format(server), "a") as main:
        #    for incl in re.findall(r"(?:^i|^ +i)nclude (.+);$",
        #                           config, re.M):
        #        main.write("\n{0}".format(
        #            check_output(["ssh", "{0}.example.com".format(server),
        #                          "cat", "/etc/nginx/{0}".format(incl)])
        #        ))

        #call(["scp",
        #      "{0}.example.com:/etc/haproxy/haproxy.cfg".format(server),
        #      "./configs/haproxy.{0}.all".format(server)])

if __name__ == "__main__":
    main()
