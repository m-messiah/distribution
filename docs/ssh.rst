Замена GitLab
=============

.. function:: fetch(configs_dir)

    Функция, в которой осуществляется вся предварительная выгрузка конфигурационных файлов для анализа.

В секции GitLab вызывается функция ``fetch_git()``, которая отвечает за выгрузку из Git.
Можно исправить ее, или добавить свою секцию в конфигурационный файл и дописать еще одну функцию.

Например, для прямого получения по ssh можно использовать что-то вроде:

..  code:: python

    def fetch_ssh(self):
        from subprocess import call, check_output

        # Imported in __init__.py
        # from os.path import join as pjoin

        for server in servers:
            call([
                "scp",
                "%s.example.com:/etc/nginx/nginx.conf" % server,
                pjoin(self.configs, "nginx.%s.all" % server)
            ])
            config = open(pjoin(self.configs, "nginx.%s.all" % server), "r").read()

            with open(pjoin(self.configs, "nginx.%s.all" % server), "a") as main:
                for incl in re.findall(r"(?:^i|^ +i)nclude (.+);$", config, re.M):
                    inc_conf = check_output([
                        "ssh", "%s.example.com" % server,
                        "cat", "/etc/nginx/%s" % incl
                    ])
                    config = config.replace("include " + incl + ";", inc_conf)
                main.write(conf)

            call(["scp",
                  "%s.example.com:/etc/haproxy/haproxy.cfg" % server,
                  pjoin(self.configs, "haproxy.%s.all" % server)])