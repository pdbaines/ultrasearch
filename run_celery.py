import json

from celery import chain, signature

from ingest.ultrasignup import UltrasignupIngest
from ingest.ahotu import AhotuIngest
from client import connect

## Note: this import is required, even though app is not used
from ingest.tasks import app


if __name__ == '__main__':

    client = connect()

    active = {
        "ultrasignup": {
            "run": True,
            "ingest": UltrasignupIngest
        },
        "ahotu": {
            "run": True,
            "ingest": AhotuIngest
        }
    }
    max_batches = 50000

    print(f"Config: {active}")
    print(f"Max batches: {max_batches}")

    for source in ["ultrasignup", "ahotu"]:
        if not active[source]["run"]:
            continue

        uti = active[source]["ingest"]()
        uti_requests = uti.fetch()

        # Submit all tasks to celery, workers will start to churn through
        # these immediately. Number of workers controls parallelism.
        print(f"Submitting {source} fetch tasks to celery")
        results = []
        for i, batch in enumerate(uti_requests):
            results.append(chain(
                signature(
                    f'{source}_fetcher',
                    kwargs={
                        "url": batch.url,
                        "request_params": json.dumps(batch.params)
                    }) |
                signature(f'{source}_parser') |
                signature(f'{source}_uploader')
            )())
            if (i + 1) >= max_batches:
                break
        print(f"All {source} tasks submitted ({len(uti_requests)} task chains)")
