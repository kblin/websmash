from flask import Flask, g
from flask_mail import Mail

from urllib.parse import urlparse
from redis import Redis
from redis.sentinel import Sentinel

app = Flask(__name__)
import websmash.default_settings
app.config.from_object(websmash.default_settings)
app.config.from_envvar('WEBSMASH_CONFIG', silent=True)
mail = Mail(app)


def get_db():
    redis_store = getattr(g, '_database', None)
    if redis_store is None:
        if 'FAKE_DB' in app.config and app.config['FAKE_DB']:
            from mockredis import mock_redis_client
            redis_store = g._database = mock_redis_client(encoding='utf-8', decode_responses=True)
        else:
            if app.config['REDIS_URL'].startswith('redis://'):
                redis_store = g._database = Redis.from_url(app.config['REDIS_URL'], encoding='utf-8',
                                                           decode_responses=True)
            elif app.config['REDIS_URL'].startswith('sentinel://'):
                parsed_url = urlparse(app.config['REDIS_URL'])
                service = parsed_url.path.lstrip('/')
                port = 26379
                if ':' in parsed_url.netloc:
                    host, str_port = parsed_url.netloc.split(':')
                    port = int(str_port)
                else:
                    host = parsed_url.netloc
                sentinel = Sentinel([(host, port)], socket_timeout=0.1)
                redis_store = sentinel.master_for(service, redis_class=Redis, socket_timeout=0.1)
    return redis_store

import websmash.api
import websmash.error_handlers
