import json

from celery import Celery

from ingest.ultrasignup import fetch_data as fetch_ultrasignup_data


## TODO: Conditional setup of either local or remote broker depending on env vars
app = Celery('foo')
app.config_from_object('ingest.celery_local_config')


@app.task(name='ultrasignup_fetcher')
def ultrasignup_fetch(url, request_params):
    return fetch_ultrasignup_data(
        url=url,
        request_params=json.loads(request_params))