Замена GitLab
=============

.. function:: get_configs(configs_dir)

    Функция, в которой осуществляется вся предварительная выгрузка конфигурационных файлов для анализа.

Именно здесь необходимо изменить секцию # Gitlab на удобный способ получения конфигов.

Например, для прямого получения по ssh можно использовать что-то вроде:

..  code:: python

    from subprocess import call, check_output
    for server in servers:
        call([
            "scp",
            "{0}.example.com:/etc/nginx/nginx.conf".format(server),
            "./configs/nginx.{0}.all".format(server)
        ])
        config = open("./configs/nginx.{0}.all".format(server), "r").read()

        with open("./configs/nginx.{0}.all".format(server), "a") as main:
            for incl in re.findall(r"(?:^i|^ +i)nclude (.+);$",
                                   config, re.M):
                inc_conf = check_output([
                    "ssh",
                    "{0}.example.com".format(server),
                    "cat",
                    "/etc/nginx/{0}".format(incl)
                ])
                config = config.replace("include " + incl + ";", inc_conf)
            main.write(conf)

        call(["scp",
              "{0}.example.com:/etc/haproxy/haproxy.cfg".format(server),
              "./configs/haproxy.{0}.all".format(server)])