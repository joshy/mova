import logging
import os
from datetime import datetime, timedelta

from flask import Flask, g, jsonify, make_response, render_template, request
from flask_assets import Bundle, Environment

import rq_dashboard

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('mova.default_config')
app.config.from_pyfile('config.cfg')
version = app.config['VERSION'] = '0.0.1'

app.config.from_object(rq_dashboard.default_settings)
app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")


assets = Environment(app)
js = Bundle("js/jquery-3.1.0.min.js",
            "js/script.js",
            filters='jsmin', output='gen/packed.js')
assets.register('js_all', js)


@app.route('/')
def main():
    return render_template('index.html', version=app.config['VERSION'])
