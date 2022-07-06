# Ultrasearch

Backend for [Ultrasearch](https://ultrasearch.io).

## Overview

This repo is the backend for [Ultrasearch](https://ultrasearch.io).
It runs scheduled tasks to obtain data from various public APIs
that contain race information about ultramarathons, and ingests
that data to a database managed by [Supabase](https://supabase.com).

## Architecture Overview

For scalability, idempotency and modularity, we break up the
workload into fetch, parse, and upload tasks that represent
a common patter for all ingest sources.

For scalability, fault-tolerance and many more reasons, we use
[celery](https://celeryproject.org) to orchestrate the execution of
these dependent component tasks. 

* Celery:
  * RabbitMQ broker
  * Redis result store
  * Multiple queues for specific task types
  * Dedicated workers for specific queues
  * Automated retries for retryable task failures
* Scheduled job to submit chained tasks to Celery

## Deployment

Production deployment is done to k8s using manifests contained
in `.gitops` and orchestrated by GitHub actions (`.gitops`).
Kubernetes clusters is managed by [Platform9](platform9.com).

## Local Development

```commandline
conda activate ultrasearch

brew install supabase/tap/supabase

supabase init   # only needed once
supbase start   # start supbase locally

psql 'postgresql://postgres:postgres@localhost:54322/postgres'
```

## Containerized Development

Start the docker compose stack: 
```yaml
make down build tag up
```

### Running the ingest jobs

```
make compose-run
```

## Profiling

```
python -m cProfile -o ingest.prof run_ingest.py
snakeviz ingest.prof
```

## Testing

Using docker:
```
make test
```
