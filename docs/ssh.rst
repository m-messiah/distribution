Замена GitLab
=============

.. function:: fetch(configs_dir)

    Функция, в которой осуществляется вся предварительная выгрузка конфигурационных файлов для анализа.

Именно здесь необходимо изменить секцию # Gitlab на удобный способ получения конфигов.

Например, для прямого получения по ssh можно использовать что-то вроде:

..  code:: python

    from subprocess import call, check_output
    for server in servers:
        call([
            "scp",
            "%s.example.com:/etc/nginx/nginx.conf" % server,
            "%s/nginx.%s.all" % (configs_dir, server)
        ])
        config = open("%s/nginx.%s.all" % (configs_dir, server), "r").read()

        with open("%s/nginx.%s.all" % (configs_dir, server), "a") as main:
            for incl in re.findall(r"(?:^i|^ +i)nclude (.+);$", config, re.M):
                inc_conf = check_output([
                    "ssh", "%s.example.com" % server,
                    "cat", "/etc/nginx/%s" % incl
                ])
                config = config.replace("include " + incl + ";", inc_conf)
            main.write(conf)

        call(["scp",
              "%s.example.com:/etc/haproxy/haproxy.cfg" % server,
              "%s/haproxy.%s.all" % (configs_dir, server)])