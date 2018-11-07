import logging
import os
import shlex
import subprocess
from pathlib import Path

from redis import Redis
from rq import Queue, get_current_job

from dicom2nifti.convert_dicom import dicom_series_to_nifti
from mova.config import dcmtk_config, pacs_config
from mova.executor import run

logger = logging.getLogger("job")


def transfer_command(dcmkt_config, pacs_config, target, study_uid, series_uid):
    """ Constructs the first part of the transfer command to a PACS node. """
    return (
        dcmkt_config.dcmtk_bin
        + "/movescu -v -S "
        + _transfer(dcmkt_config, pacs_config, target, study_uid, series_uid)
    )


def _transfer(dcmkt_config, pacs_config, target, study_uid, series_uid):
    return "-aem {} -aet {} -aec {} {} {} -k StudyInstanceUID={} -k SeriesInstanceUID={} {}".format(
        target,
        pacs_config.ae_title,
        pacs_config.ae_called,
        pacs_config.peer_address,
        pacs_config.peer_port,
        study_uid,
        series_uid,
        dcmkt_config.dcmin,
    )


def transfer_series(config, series_list, target, queue_name):
    dcmtk = dcmtk_config(config)
    pacs = pacs_config(config)
    for entry in series_list:
        study_uid = entry["study_uid"]
        series_uid = entry["series_uid"]
        command = transfer_command(dcmtk, pacs, target, study_uid, series_uid)
        args = shlex.split(command)
        queue(args, queue_name)
        logger.debug("Running transfer command %s", args)
    return len(series_list)


def base_command(dcmtk_config, pacs_config):
    """ Constructs the first part of a dcmtk command. """
    return (
        dcmtk_config.dcmtk_bin
        + "/movescu -v -S -k QueryRetrieveLevel=SERIES "
        + "-aet {} -aec {} {} {} +P {}".format(
            pacs_config.ae_title,
            pacs_config.ae_called,
            pacs_config.peer_address,
            pacs_config.peer_port,
            pacs_config.incoming_port,
        )
    )


def download_series(config, series_list, dir_name, queue_name):
    """ Download the series. The folder structure is as follows:
        MAIN_DOWNLOAD_DIR / USER_DEFINED / PATIENTID / ACCESSION_NUMBER /
          / SERIES_NUMER
    """
    output_dir = config["IMAGE_FOLDER"]
    dcmtk = dcmtk_config(config)
    pacs = pacs_config(config)
    job_entries = []
    jobs = []
    for entry in series_list:
        image_folder = _create_image_dir(output_dir, entry, dir_name)
        study_uid = entry["study_uid"]
        series_uid = entry["series_uid"]
        command = (
            base_command(dcmtk, pacs)
            + " --output-directory "
            + image_folder
            + " -k StudyInstanceUID="
            + study_uid
            + " -k SeriesInstanceUID="
            + series_uid
            + " "
            + dcmtk.dcmin
        )
        args = shlex.split(command)
        job, q = queue(args, queue_name)
        job_entry = entry.copy()
        job_entry["job_id"] = job.id
        job_entries.append(job_entry)
        jobs.append(job)
        logger.debug("Running download command %s", args)
    return len(series_list), job_entries, jobs, q


def convert_series(config, entry, queue_name):
    _, _, jobs, q = download_series(config, [entry], "viewer", queue_name)
    k = q.enqueue(co, (config, entry), depends_on=jobs[0])
    return True


def co(input):
    config, entry = input
    print("Download complete")
    redis_conn = Redis()
    current_job = get_current_job(redis_conn)

    output_dir = config["IMAGE_FOLDER"]
    p = Path(output_dir) / "viewer" /entry["patient_id"] / entry["accession_number"] / entry["series_number"]
    dicom_series_to_nifti(p, str(p) + "/source.nii.gz")

    print("Running conversion")
    return True


def queue(cmd, queue_name):
    redis_conn = Redis()
    if queue_name:
        queue = Queue(queue_name, connection=redis_conn)
    else:
        # no args implies the default queue
        queue = Queue(connection=redis_conn)
    job = queue.enqueue(run, cmd, timeout=900)  # 15min timeout
    return job, queue


def _create_image_dir(output_dir, entry, dir_name):
    patient_id = entry["patient_id"]
    accession_number = entry["accession_number"]
    series_number = entry["series_number"]
    image_folder = os.path.join(
        output_dir, dir_name, patient_id, accession_number, series_number
    )
    if not os.path.exists(image_folder):
        os.makedirs(image_folder, exist_ok=True)
    return image_folder
