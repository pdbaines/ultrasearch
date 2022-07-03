import json

from celery import signature

from ingest.ultrasignup import UltrasignupIngest
from ingest.ahotu import AhotuIngest
from client import connect
from ingest.tasks import app

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    ultrasignup = True
    ahotu = True
    max_batches = 4

    client = connect()
    if ultrasignup:
        uti = UltrasignupIngest()
        uti_requests = uti.fetch()

        # Submit all tasks to celery, workers will start to churn through
        # these immediately. Number of workers controls parallelism.
        print("Submitting fetch tasks to celery")
        results = []
        for i, batch in enumerate(uti_requests):
            results.append(app.send_task(
                'ultrasignup_fetcher',
                kwargs={"url": batch.url, "request_params": json.dumps(batch.params)}))
            if (i + 1) >= max_batches:
                break
        print("All tasks submitted")

        # Loop over results and parse/upload them:
        for i, result in enumerate(results):
            parsed_batch = uti.parse(result.get())
            uti.upload(parsed_batch, client=client)
            if (i + 1) >= max_batches:
                break