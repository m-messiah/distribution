Конфигурация
============

Вся настройка производится через ini файл, передаваемый в параметре ``--conf (-c)``

GitLab
------

..  code:: ini

    [git]
    # Адрес gitlab сервера
    host = git.example.com
    # Ваш API токен, для доступа к репозиториям
    token = ""
    # GitLab-группа, в которой размещены репозитории с конфигами
    group = ""
    # Список серверов-названий проектов в git
    servers = eu-front1,eu-front2,us-front1,us-front2,int-front
    # Смерджит конфиги eu-front1 и eu-front2, отображая их как "eu"
    # Отображает имя сервера на .group(1) - то, что в скобках
    same_host = (\w\w\)-front\d
    # Если skipped в названии сервера, то к nginx не будут применяться проверки доступности. (например, если там локальные адреса)
    skipped = int

.. _conf-nginx:

Nginx
~~~~~

Чтобы корректно отображалась колонка автора в **Distributor** необходимо, чтобы хотя бы в одной строке внутри блока ``server {}`` в конце строки присутсвовал комментарий с текстом ``author: <author>``.
Например, удобно обозначать e-mail автора для более быстрого рагирования по инцидентам:

..  code:: nginx

    server {
        server_name www.example.com; # author: webmaster@example.com
        listen 80;
        location / {...};
    }

Отдельные приложения можно вынести в группу ``promo`` и они будут более тщательно проверяться **Distributor**. Маркер promo также необходимо использовать в комментариях в секции ``server {}``.
Можно расширить предыдущий пример:

..  code:: nginx

    server {
        server_name www.example.com; # promo author: webmaster@example.com
        listen 80;
        location / {...};
    }

Осуществляемые проверки описаны на странице :ref:`checks-main`


BIND/DNS
--------

Сейчас DNS трансфер зон осуществляется с использованием TSIG ключа:

..  code:: ini

    [dns]
    server = ns.example.com
    tsig_type = HMAC-SHA512
    tsig_name = TSIGKEY
    tsig_key = STRONGKEY==
    # Список зон, которые необходимо трансферить и отображать.
    domains = example.com,example.net

NIC.ru
------

Возможно использование **Distributor** для получения информации о делегировании доменов, зарегистрированных в nic.ru, с последующей проверкой их SOA на соответствие реальности и проверкой на наличие SPF и DMARC записей у зон.
Для этого необходимо вписать свой логин и пароль от ЛК nic.ru (на данный момент у них нет АПИ, позволявшего бы получить ту же информацию):

..  code:: ini

    [nic]
    login = 123456
    password = password