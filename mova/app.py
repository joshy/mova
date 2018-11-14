import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import rq_dashboard
from flask import Flask, jsonify, render_template, request, send_file
from flask_assets import Bundle, Environment

from mova.config import dcmtk_config, pacs_config
from mova.job import download_series, transfer_series

app = Flask(__name__, instance_relative_config=True)
app.config.from_object("mova.default_config")
app.config.from_pyfile("config.cfg")
version = app.config["VERSION"] = "1.0.0"

app.config.from_object(rq_dashboard.default_settings)
app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")

assets = Environment(app)
js = Bundle(
    "js/jquery-3.3.1.min.js", "js/papaya.js", "js/script.js", filters="jsmin", output="gen/packed.js"
)
assets.register("js_all", js)


@app.route("/")
def main():
    return render_template("index.html", version=app.config["VERSION"])


@app.route("/download", methods=["POST"])
def download():
    """ Post to download series of images. """
    app.logger.info("download called")
    data = request.get_json(force=True)
    series_list = data.get("data", "")
    dir_name = data.get("dir", "")
    queue_name = data.get("queue", "")
    length, jobs, _ = download_series(app.config, series_list, dir_name, queue_name)
    return json.dumps({"status": "OK", "series_length": length, "jobs": jobs})


@app.route("/transfer", methods=["POST"])
def transfer():
    """ Post to transfer series of images to another PACS node. """
    data = request.get_json(force=True)
    target = data.get("target", "")
    series_list = data.get("data", "")
    app.logger.info("transfer called and sending to %s", target)
    queue_name = data.get("queue", "")
    study_size = transfer_series(app.config, series_list, target, queue_name)
    return str(study_size)


@app.route("/view")
def view():
    patient_id = request.args.get("patient_id")
    accession_number = request.args.get("accession_number")
    series_number = request.args.get("series_number")
    study_description = request.args.get('study_description')
    series_description = request.args.get('series_description')

    # for CR modality viewer shows only one view, used in frontend
    cr_modality = request.args.get('modality') == "CR"
    entry = {}
    entry["study_uid"] = request.args.get("study_uid")
    entry["series_uid"] = request.args.get("series_uid")
    entry["patient_id"] = patient_id
    entry["accession_number"] = accession_number
    entry["series_number"] = series_number
    entry["study_description"] = study_description
    entry["series_description"] = series_description

    output_dir = app.config["IMAGE_FOLDER"]
    p = Path(output_dir) / "viewer" / patient_id / accession_number / series_number
    list = p.glob("*")
    files = ["/images" + str(x) for x in list if x.is_file()]

    job_id = None
    if len(files) <= 0:
        _, job_entries, jobs, q = download_series(app.config, [entry], "viewer", "viewer")
        # viewing is only supported for one series!
        job_id = jobs[0].id

    return render_template("view.html", source_image=json.dumps(files), result=entry, cr_modality=cr_modality, job_id=job_id)


@app.route("/images/<path:path>")
def images(path):
    output_dir = app.config["IMAGE_FOLDER"]
    f = os.path.join(output_dir, path)
    x = Path(path)
    return send_file("/" + str(x), mimetype="appliaction/dicom")
