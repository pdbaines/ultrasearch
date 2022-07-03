FROM python:3.10

RUN pip install poetry==1.1.13

RUN mkdir /app
RUN groupadd -g 1000 ultrasearchers
RUN useradd -s /bin/bash --create-home --uid 1000 --gid 1000 ultrasearcher

RUN chown -R 1000:1000 /app
USER ultrasearcher:ultrasearchers

WORKDIR /app
COPY poetry.lock pyproject.toml /app/
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

ENV PATH="/home/ultrasearcher/.local/bin:${PATH}"
COPY ingest/ /app/ingest/
COPY client.py \
    events.py \
    run_ingest.py \
    run_celery.py \
    /app/

CMD ["python", "run_ingest.py"]
