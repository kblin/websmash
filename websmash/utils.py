#!/usr/bin/env python
"""Utility functions for websmash"""
import os

from flask import request
from os import path
import platform
import uuid

import werkzeug.utils
from antismash_models import SyncJob as Job

from websmash import app, get_db, DataStore
from websmash.error_handlers import BadRequest


def generate_confirmation_mail(message):
    """Generate confirmation email message from template"""
    confirmation_template = """We have received your feedback to antiSMASH and will reply to you as soon as possible.
Your message was:

%s
"""
    return confirmation_template % message


def _generate_jobid(taxon: str) -> str:
    """Generate a job uid based on the taxon"""
    return "{}-{}".format(taxon, uuid.uuid4())


def _add_to_queue(redis_store, job):
    """Add job to a specified job queue"""
    queue = job.target_queues.pop()
    job.commit()
    redis_store.lpush(queue, job.job_id)


def _submit_job(redis_store, job, config):
    """Submit a new job"""
    job.state = 'queued'
    limit = config['MAX_JOBS_PER_USER']

    job.target_queues.append(config['DEFAULT_QUEUE'])

    if job.email and _count_pending_jobs_with_email(redis_store, job) > limit:
        _waitlist_job(job, job.email)
    elif _count_pending_jobs_with_ip(redis_store, job) > limit:
        _waitlist_job(job, job.ip_addr)

    if job.needs_download:
        job.target_queues.append(config['DOWNLOAD_QUEUE'])
    _add_to_queue(redis_store, job)


def _count_pending_jobs_with_email(redis_store: DataStore, job: Job) -> int:
    """Count how many jobs are pending for the email of the current job"""
    count = 0
    for job_id in redis_store.lrange(app.config['DEFAULT_QUEUE'], 0, -1):
        job_key = "job:{}".format(job_id)
        if redis_store.hget(job_key, 'email') == job.email:
            count += 1
    for job_id in redis_store.lrange(app.config['LEGACY_QUEUE'], 0, -1):
        job_key = "job:{}".format(job_id)
        if redis_store.hget(job_key, 'email') == job.email:
            count += 1

    return count


def _count_pending_jobs_with_ip(redis_store: DataStore, job: Job) -> int:
    """Count how many jobs are pending for the IP address of the current job"""
    count = 0
    for job_id in redis_store.lrange(app.config['DEFAULT_QUEUE'], 0, -1):
        job_key = "job:{}".format(job_id)
        if redis_store.hget(job_key, 'ip_addr') == job.ip_addr:
            count += 1
    for job_id in redis_store.lrange(app.config['LEGACY_QUEUE'], 0, -1):
        job_key = "job:{}".format(job_id)
        if redis_store.hget(job_key, 'ip_addr') == job.ip_addr:
            count += 1

    return count


def _waitlist_job(job, attribute):
    """Put the given job on a waitlist"""
    job.state = 'waiting'
    job.status = 'waiting: Too many jobs in queue for this user.'
    waitlist = '{}:{}'.format(app.config['WAITLIST_PREFIX'], attribute)
    job.target_queues.append(waitlist)


def _get_checkbox(req, name):
    """Get True/False value for the checkbox of a given name"""
    str_value = req.form.get(name, u'off')
    return str_value == u'on' or str_value == 'true'


def dispatch_job():
    """Internal helper to dispatch a new job"""
    redis_store = get_db()
    taxon = app.config['TAXON']
    job_id = _generate_jobid(taxon)

    job = Job(redis_store, job_id)

    if 'X-Forwarded-For' in request.headers:
        job.ip_addr = request.headers.getlist("X-Forwarded-For")[0].rpartition(' ')[-1]
    else:
        job.ip_addr = request.remote_addr or 'untrackable'

    ncbi = request.form.get('ncbi', '').strip()

    val = request.form.get('email', '').strip()
    if val:
        job.email = val

    job.jobtype = request.form.get('jobtype', "")
    if not job.jobtype.startswith("experimentalsmash-"):
        raise BadRequest(f"Invalid jobtype {job.jobtype}")

    genefinder = request.form.get('genefinder', '')
    if genefinder:
        job.genefinder = genefinder

    dirname = path.join(app.config['RESULTS_PATH'], job.job_id, 'input')
    os.makedirs(dirname)

    if ncbi != '':
        if ' ' in ncbi:
            raise BadRequest("Spaces are not allowed in an NCBI ID.")
        job.download = ncbi
        job.needs_download = True
    else:
        upload = request.files['seq']

        if upload is not None:
            filename = secure_filename(upload.filename)
            upload.save(path.join(dirname, filename))
            if not path.exists(path.join(dirname, filename)):
                raise BadRequest("Could not save file!")
            job.filename = filename
            job.needs_download = False
        else:
            raise BadRequest("Uploading input file failed!")

        if 'gff3' in request.files:
            gff_upload = request.files['gff3']
            if gff_upload is not None:
                gff_filename = secure_filename(gff_upload.filename)
                gff_upload.save(path.join(dirname, gff_filename))
                if not path.exists(path.join(dirname, gff_filename)):
                    raise BadRequest("Could not save GFF file!")
                job.gff3 = gff_filename

    job.trace.append("{}-api".format(platform.node()))

    _submit_job(redis_store, job, app.config)
    return job


def secure_filename(name: str) -> str:
    """Even more secure filenames"""
    secure_name = werkzeug.utils.secure_filename(name)
    secure_name = secure_name.lstrip('-')
    return secure_name
