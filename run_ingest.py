from ingest.ultrasignup import UltrasignupIngest
from ingest.ahotu import AhotuIngest
from client import connect


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    ultrasignup = True
    ahotu = True
    max_batches = 4

    client = connect()

    if ultrasignup:
        uti = UltrasignupIngest()
        uti_requests = uti.fetch()
        for i, batch in enumerate(uti_requests):
            parsed_batch = uti.parse(batch.fetch())
            uti.upload(parsed_batch, client=client)
            if i >= max_batches:
                break

    if ahotu:
        ahi = AhotuIngest()
        ahotu_requests = ahi.fetch()
        for i, batch in enumerate(ahotu_requests):
            parsed_batch = ahi.parse(batch.fetch())
            ahi.upload(parsed_batch, client=client)
            if i >= max_batches:
                break
