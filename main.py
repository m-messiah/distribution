#!/usr/bin/python
# -*- coding:utf-8 -*-
__author__ = 'Maxim Muzafarov'
import logging

from flask import Flask, redirect, session, render_template, flash
from flask_ldap import LDAP, login_required
from markupsafe import Markup
from os import urandom
import distributor
import syncer


logging.basicConfig(filename='/var/log/distribution.log',
                    format='%(asctime)-15s %(levelname)s %(message)s',
                    level=logging.INFO)

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('settings.py')
app.PREFIX = ""
app.distributor = distributor.Distributor()

ldap = LDAP(app)
app.secret_key = urandom(64)
app.add_url_rule("{}/login".format(app.PREFIX), 'login',
                 ldap.login, methods=['GET', 'POST'])


@app.route("{}/".format(app.PREFIX))
@login_required
def index():
    panes = []
    for cat in sorted(app.distributor.services.keys()):
        if cat == "web" or cat == "other":
            continue
        panes.append({"href": cat, "name": cat.title(),
                      "content": Markup(generator(cat))})
    #logging.info('User {} loaded root'.format(current_user.email))
    return render_template("index.html", panes=panes,
                           webpane=Markup(generator("web")),
                           otherpane=Markup(generator("other")),
                           last_sync=app.distributor.last_sync)


@app.route('{}/refresh'.format(app.PREFIX))
@login_required
def refresh():
    #reload(syncer)
    #syncer.main()
    reload(distributor)
    app.distributor = distributor.Distributor()
    return redirect('{}/'.format(app.PREFIX))


def generator(category):
    try:
        response = app.distributor.write(category)
    except:
        response = u"<h1>No such category '{}'</h1>".format(category)
    return response


@app.route("{}/logout".format(app.PREFIX))
@login_required
def logout():
    session.pop('username', None)
    flash('Good bye!')
    return redirect("{}/".format(app.PREFIX))


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", error=error), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082, debug=True)
