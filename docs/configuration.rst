Конфигурация
============


GitLab
------

Для использования со своим GitLab сервером, необходимо создать файл `settings.py` с обьявлением переменных:

..  code:: python

    GIT_HOST = git.example.com # Адрес gitlab сервера
    GIT_TOKEN = "" # Ваш API токен, для доступа к репозиториям
    GIT_GROUP = "" # GitLab-группа, в которой размещены репозитории с конфигами
    SERVERS = ['eu-front1', 'eu-front2', 'us-front1', 'us-front2', 'int-front'] # Список серверов-названий проектов в git
    SAME_HOST = "\w\w\-front\d" # Смерджит конфиги eu-front1 и eu-front2, отображая их как "eu"
    SKIPPED = "int" # Если SKIPPED в названии сервера, то к nginx не будут применяться проверки доступности. (например, если там локальные адреса)

.. _conf-nginx:
Nginx
~~~~~

Чтобы корректно отображалась колонка автора в **Distributor** необходимо, чтобы хотя бы в одной строке внутри блока server {} в конце строки присутсвовал комментарий с текстом `author: <author>`.
Например, удобно обозначать e-mail автора для более быстрого рагирования по инцидентам:

..  code:: nginx

    server {
        server_name www.example.com; # author: webmaster@example.com
        listen 80;
        location / {...};
    }

Отдельные приложения можно вынести в группу `promo` и они будут более тщательно проверяться **Distributor**. Маркер promo также необходимо использовать в комментариях в секции server {}.
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

Сейчас DNS трансфер зон осуществляется с использованием TSIG ключа, который также необходимо указать в `settings.py`:

..  code:: python

    DNS_SERVER = 'ns.example.com'
    TSIG_TYPE = 'HMAC-SHA512'
    TSIG_NAME = 'TSIGKEY'
    TSIG_KEY = 'STRONGKEY=='
    DOMAINS = ["example.com", "example.net"] # Список зон, которые необходимо трансферить и отображать.

NIC.ru
------

Возможно использование **Distributor** для получения информации о делегировании доменов, зарегистрированных в nic.ru, с последующей проверкой их SOA на соответствие реальности и проверкой на наличие SPF и DMARC записей у зон.
Для этого также необходимо в `settings.py` вписать свой логин и пароль от ЛК nic.ru (на данный момент у них нет АПИ, позволявшего бы получить ту же информацию):

..  code:: python

    NIC_LOGIN = '123456'
    NIC_PASSWORD = 'password'