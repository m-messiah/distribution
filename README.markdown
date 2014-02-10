# Distribution #

*Let me show, where your service*

## What is it? ##

When you have many frontend servers - it's a big headache to know, which of them listens your service now, especcially, if you recently moved some services between frontend balancers.

**Distribution** is a web app, which can get Nginx and HAproxy configurations from your frontend servers,
and clearly show which of your frontends listen each service and ip address.

## How it works? ##

**Distribution** is a Flask app with FCGI wrapper.
**Distribution** must have SSH access to your frontend servers (code in comments),
or it must have access to your GIT server, where your frontends push their /etc/{nginx,haproxy} files.
**Distribution** is configured now for using LDAP, but you can remove auth at all.

## Run ##
###If you have LDAP server ###
Simply edit **instance/settings.py** for your LDAP server address, domain, search base, and required group (if needed), and you will can authenticate to this app.

###If you have GIT server with configs###
Add your PRIVATE_TOKEN in **syncer.py** to get access repositories and fix url of your git server.

###If you doesn't have git server###
Configure ssh access to servers without password [Google](https://www.google.ru/search?client=safari&rls=en&q=ssh+without+password&ie=UTF-8&oe=UTF-8&gws_rd=cr&ei=Grf4Up-4D4La4wTcjYAY)

Delete 12-22 lines from **syncer.py** and uncomment others.
Configure your addresses.

###Finish###
Start **Distribution** as Flask app (*python main.py*) or handle it as PythonFCGI (*lighttpd* or other)
