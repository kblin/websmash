"""REST-like API for submitting and querying antiSMASH-style jobs"""

from datetime import datetime
from antismash_models import SyncJob as Job, SyncNotice as Notice
from flask import jsonify, abort, request
from flask_mail import Message

from websmash import app, get_db, mail, git_version
from websmash.utils import dispatch_job


@app.route('/api/v1.0/version')
def get_version():
    """Return version information"""
    version_dict = {
        'api': '1.0.0',
        'antismash_generation': app.config['DEFAULT_JOBTYPE'][-1],
        'taxon': app.config['TAXON'],
        'git': git_version,
    }
    return jsonify(version_dict)


@app.route('/api/v1.0/submit', methods=['POST'])
def api_submit():
    """Submit a new antiSMASH job via an API call"""
    job = dispatch_job()
    return jsonify(dict(id=job.job_id))


@app.route('/api/v1.0/stats')
def get_stats():
    redis_store = get_db()
    pending = redis_store.llen(app.config['DEFAULT_QUEUE'])
    running = redis_store.llen('jobs:running')

    # carry over jobs count from the old database from the config
    total_jobs = app.config['OLD_JOB_COUNT'] + redis_store.llen('jobs:completed') + \
        redis_store.llen('jobs:failed') + redis_store.llen('jobs:removed')

    if pending + running > 0:
        status = 'working'
    else:
        status = 'idle'

    ts_queued, ts_queued_m = _get_job_timestamps(_get_oldest_job(app.config['DEFAULT_QUEUE']))

    return jsonify(status=status, queue_length=pending, running=running,
                   total_jobs=total_jobs,
                   ts_queued=ts_queued, ts_queued_m=ts_queued_m)


def _get_oldest_job(queue):
    """Get the oldest job in a queue"""
    redis_store = get_db()
    try:
        job_id = redis_store.lrange(queue, -1, -1)[0]
    except IndexError:
        return None

    job = Job(redis_store, job_id)
    job.fetch()
    return job


def _get_job_timestamps(job):
    """Get both a readable and a machine-readable timestamp for a job"""
    if job is None:
        return None, None
    return job.last_changed.strftime("%Y-%m-%d %H:%M"), job.last_changed.strftime("%Y-%m-%dT%H:%M:%SZ")


@app.route('/api/v1.0/news')
def get_news():
    """Display current notices"""
    redis_store = get_db()
    notices = []
    for notice_id in redis_store.keys('notice:*'):
        notice = Notice(redis_store, notice_id[7:])
        try:
            notice.fetch()
        except ValueError:
            continue

        if notice.show_from > datetime.utcnow():
            # show_from is in the future, don't show this yet
            continue

        notices.append(notice.to_dict())

    return jsonify(notices=notices)


@app.route('/api/v1.0/status/<task_id>')
def status(task_id):
    redis_store = get_db()
    job = Job(redis_store, task_id)
    try:
        job.fetch()
    except ValueError:
        # TODO: Write a json error handler for 404 errors
        abort(404)

    res = job.to_dict()

    if job.state == 'done':
        result_url = "%s/%s/index.html" % (app.config['RESULTS_URL'], job.job_id)
        res['result_url'] = result_url
    res['added_ts'] = job.added.strftime("%Y-%m-%dT%H:%M:%SZ")
    res['last_changed_ts'] = job.last_changed.strftime("%Y-%m-%dT%H:%M:%SZ")
    # TODO: This fixes old web UIs while stupid browser caching is going on. Can be removed soon, I hope.
    # I hate browser caches.
    res['short_status'] = job.state

    return jsonify(res)


@app.route('/api/v1.0/email/send', methods=['POST'])
def send_email():
    if 'email' not in request.json:
        abort(400)
    email = request.json['email']

    if 'message' not in request.json:
        abort(400)
    message = request.json['message']

    with mail.connect() as conn:
        feedback_message = Message(subject="antiSMASH feedback",
                                   recipients=app.config['DEFAULT_RECIPIENTS'],
                                   body=message, sender=email)

        conn.send(feedback_message)

        confirmation_msg = Message(subject='antiSMASH feedback received',
                                   recipients=[email],
                                   body="We have received your feedback to antiSMASH "
                                        "and will reply to you as soon as possible.")
        conn.send(confirmation_msg)

    return '', 204
