Использование
=============

Установка
---------

..  code:: bash

    pip install distributor


Кроме того, вам может понадобиться веб-сервер для раздачи статических html файлов.


Запуск
------

..  code:: bash

    sudo -u www-data distributor-gen -c config.ini -l distributor.log -o /var/www/
