from ingest.ingest import UltrasignupIngest
from client import connect


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    client = connect()
    uti = UltrasignupIngest()
    uti.fetch()
    uti.parse()
    uti.upload(client=client)
