from ingest.ultrasignup import UltrasignupIngest
from ingest.ahotu import AhotuIngest
from client import connect


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    ultrasignup = False
    ahotu = True
    max_batches = 100
    parse_skip_index = 64

    client = connect()

    if ultrasignup:
        batch_ctr = 0
        uti = UltrasignupIngest()
        for batch in uti.fetch():
            batch_ctr += 1
            # Allow skipping for resumption:
            if batch_ctr < parse_skip_index:
                continue
            parsed_batch = uti.parse(batch)
            uti.upload(parsed_batch, client=client)
            if batch_ctr >= max_batches:
                break

    if ahotu:
        ahi = AhotuIngest()
        batch_ctr = 0
        for batch in ahi.fetch():
            batch_ctr += 1
            # Allow skipping for resumption:
            if batch_ctr < parse_skip_index:
                continue
            parsed_batch = ahi.parse(batch)
            ahi.upload(parsed_batch, client=client)
            if batch_ctr >= max_batches:
                break
