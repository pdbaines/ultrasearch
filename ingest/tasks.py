import json
import os

import httpcore
import httpx
from celery import Celery

from events import event_list_dumps

from ingest.ultrasignup import fetch_data as fetch_ultrasignup_data
from ingest.ultrasignup import parse_data as parse_ultrasignup_data
from ingest.ultrasignup import upload_data as upload_ultrasignup_data
from ingest.ahotu import fetch_data as fetch_ahotu_data
from ingest.ahotu import parse_data as parse_ahotu_data
from ingest.ahotu import upload_data as upload_ahotu_data

from kombu import serialization


serialization.register(
    'event_parser_serializer',
    event_list_dumps,
    json.loads,
    content_type='json',
    content_encoding='utf-8',
)

FETCH_QUEUE = 'fetch'
PARSE_QUEUE = 'parse'
UPLOAD_QUEUE = 'upload'

app = Celery(
    'foo',
    broker=os.getenv('BROKER_URL'),
    backend=os.getenv('RESULT_BACKEND'),
    accept_content=[
        'json',
        'event_parser_serializer'
    ],
    task_routes={
        'ultrasignup_fetcher': {'queue': FETCH_QUEUE},
        'ahotu_fetcher': {'queue': FETCH_QUEUE},
        'ultrasignup_parser': {'queue': PARSE_QUEUE},
        'ahotu_parser': {'queue': PARSE_QUEUE},
        'ultrasignup_uploader': {'queue': UPLOAD_QUEUE},
        'ahotu_uploader': {'queue': UPLOAD_QUEUE}
    }
)

# =============================================================================
# Ultrasignup tasks:
# =============================================================================


@app.task(name='ultrasignup_fetcher')
def ultrasignup_fetch(url, request_params):
    return fetch_ultrasignup_data(
        url=url,
        request_params=json.loads(request_params))


@app.task(
    name='ultrasignup_parser',
    serializer='event_parser_serializer')
def ahotu_parser(batch):
    return parse_ultrasignup_data(batch)


@app.task(
    name='ultrasignup_uploader',
    throws=(
        httpcore.ReadTimeout,
        httpx.ReadTimeout,
    ),
    auto_retry_for=(
        httpcore.ReadTimeout,
        httpx.ReadTimeout,
    ),
    max_retries=3,
    retry_backoff=True)
def ahotu_uploader(batch):
    return upload_ultrasignup_data(batch)

# =============================================================================
# Ahotu tasks:
# =============================================================================


@app.task(name='ahotu_fetcher')
def ahotu_fetch(url, request_params):
    return fetch_ahotu_data(
        url=url,
        request_params=json.loads(request_params))


@app.task(
    name='ahotu_parser',
    serializer='event_parser_serializer')
def ahotu_parser(batch):
    return parse_ahotu_data(batch)


@app.task(
    name='ahotu_uploader',
    throws=(
        httpcore.ReadTimeout,
        httpx.ReadTimeout,
    ),
    auto_retry_for=(
        httpcore.ReadTimeout,
        httpx.ReadTimeout),
    max_retries=3,
    retry_backoff=True)
def ahotu_uploader(batch):
    return upload_ahotu_data(batch)
