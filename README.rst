Distributor
===========

..  epigraph::
    *"Let me show, where your service"*
    

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
    
    
What is it?
-----------

When you have many frontend servers - it's a big headache to know, which of them listens your service now, especially, if you often need to move some services between groups of frontend balancers.
Moreover, if you have so many domain names, it is also difficult to monitor their actuality without automatic systems.
 
**Distributor** is a web app, which can get Nginx and HAproxy configurations from your frontend servers, and clearly show which of your frontends listen each service and ip address.

How it works?
-------------

**Distributor** can get configs from GitLab, where frontends push their Nginx and HAproxy configs, also it can get dns zone transfers and handle list of your domains from nic.ru. 

If your fronts doesn't push their configs, you need to customize code to get configs from other places.

Usage
-----

..  code:: bash

    sudo -u www-data distributor-gen -c config.ini -l distributor.log -o /var/www/
    
Where config.ini is your config file as described in documentation, and /var/www/ is the directory, which published by some static web-server.