from ingest.ultrasignup import UltrasignupIngest
from ingest.ahotu import AhotuIngest
from client import connect


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    ultrasignup = True
    ahotu = True
    max_batches = 3

    client = connect()

    if ultrasignup:
        batch_ctr = 0
        uti = UltrasignupIngest()
        for batch in uti.fetch():
            parsed_batch = uti.parse(batch)
            uti.upload(parsed_batch, client=client)
            batch_ctr += 1
            if batch_ctr >= max_batches:
                break

    if ahotu:
        ahi = AhotuIngest()
        batch_ctr = 0
        for batch in ahi.fetch():
            parsed_batch = ahi.parse(batch)
            ahi.upload(parsed_batch, client=client)
            batch_ctr += 1
            if batch_ctr >= max_batches:
                break
