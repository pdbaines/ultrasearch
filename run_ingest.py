from ingest.ultrasignup import UltrasignupIngest
from ingest.ahotu import AhotuIngest
from client import connect


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    ultrasignup = False
    ahotu = True

    client = connect()

    if ultrasignup:
        uti = UltrasignupIngest()
        uti.fetch()
        uti.parse()
        uti.upload(client=client)

    if ahotu:
        ahi = AhotuIngest()
        ahi.fetch(max_pages=2)
        ahi.parse()
        ahi.upload(client=client)
