import os
import json


def track(job_id, path):
    d = {"destination": str(path)}
    with open("work/{}.json".format(job_id), "w") as job_file:
        json.dump(d, job_file)


def check(job_id):
    """ Returns file path to check for dicom files. """
    with open("work/{}.json".format(job_id)) as job_file:
        d = json.load(job_file)
        return d["destination"]

