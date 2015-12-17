Документация Distributor
========================

.. epigraph::
    *"Покажи мне где твои сервисы и я скажу, что ты ошибаешься."*


.. image:: https://img.shields.io/pypi/v/distributor.svg?style=flat-square
    :target: https://pypi.python.org/pypi/distributor
    :alt: PyPI latest version

.. image:: https://img.shields.io/pypi/dm/distributor.svg?style=flat-square
    :target: https://pypi.python.org/pypi/distributor
    :alt: PyPI downloads/month

.. image:: https://img.shields.io/travis/m-messiah/distributor.svg?style=flat-square
    :target: https://travis-ci.org/m-messiah/distributor

.. image:: https://readthedocs.org/projects/distributor/badge/?version=latest&style=flat-square
    :target: http://distributor.readthedocs.org/ru/latest/?badge=latest
    :alt: Documentation Status


Когда у вас много серверов-фронтов, попытка уследить какие адреса и приложения слушаются на каком из них становится большой головнй болью, в особенности, если необходимо часто перемещать различные приложения между разными группами балансировщиков.
Более того, при таком количестве доменов, уследить за их актуальности также не представляется возможным без использования автоматизации.

**Distributor** - это утилита, которая получает конфигурацию Nginx и Haproxy, умеет получать трансферы DNS зон, и получать список доменов с NIC.ru, после чего строит из всего этого удобную веб-страничку с соответсвиями между сервисами.

Как это работает?
-----------------

В текущей версии **Distributor** умеет забирать конфигурационные файлы с GitLab, куда балансировщики пушат свою конфигурацию.

Если возможности и желания реализовывать такую схему нет, необходима кастомизация кода.


..  toctree::
    :maxdepth: 1
    :caption: Стандартное использование

    Конфигурация <configuration>
    Использование <usage>
    Проверки <checks>

..  toctree::
    :maxdepth: 1
    :caption: Кастомизация

    Замена GitLab <ssh>