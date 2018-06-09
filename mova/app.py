import json
import logging
import os
from datetime import datetime, timedelta

import rq_dashboard
from flask import Flask, jsonify, render_template, request
from flask_assets import Bundle, Environment

from mova.config import dcmtk_config, pacs_config
from mova.job import download_series

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('mova.default_config')
app.config.from_pyfile('config.cfg')
version = app.config['VERSION'] = '0.0.1'

app.config.from_object(rq_dashboard.default_settings)
app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")

assets = Environment(app)
js = Bundle(
    "js/jquery-3.3.1.min.js",
    "js/script.js",
    filters='jsmin',
    output='gen/packed.js')
assets.register('js_all', js)


@app.route('/')
def main():
    return render_template('index.html', version=app.config['VERSION'])


@app.route('/receive', methods=['POST'])
def receive():
    """ Ajax post to download series of images. """
    app.logger.info("download called")
    data = request.get_json(force=True)
    # list of objects with following keys
    # "patient_id", "study_id", "series_id",
    # "accession_number", "series_number"
    # see script.js
    series_list = data.get('data', '')
    dir_name = data.get('dir', '')
    length = download_series(app.config, series_list, dir_name)
    return json.dumps({'status': 'OK', 'series_length': length})
