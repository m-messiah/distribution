Использование
=============

Установка
---------

..  code:: bash

    pip install distributor

Может использоваться как с Python2.7+, так и с Python3+.

Кроме того, вам может понадобиться веб-сервер для раздачи статических html файлов.


Запуск
------

..  code:: bash

    sudo -u www-data distributor-gen -c config.ini -l distributor.log -o /var/www/

Пример использования
--------------------

..  code:: bash

    # /etc/crontab
    # Daily distributor-gen
    0 5 * * * nginx /usr/bin/distributor-gen -c /etc/distributor.conf -o /var/www/distributor -l /var/www/distributor/log