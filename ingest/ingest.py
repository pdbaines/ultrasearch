# Request ultrasignup
# Insert returned values into database
# Abstract for source
from abc import ABC, abstractmethod
import logging as log
import os

import httpx
from supabase import Client

from ingest.parser import distance_parser, distance_extract, identity


log.basicConfig(level=log.INFO)


class Ingest(ABC):

    @abstractmethod
    def fetch(self) -> None:
        pass

    @abstractmethod
    def parse(self) -> None:
        pass

    @abstractmethod
    def upload(self, client: Client) -> None:
        pass


SCHEMA_MAPPING = {
    "source_id": (None, identity),
    "name": ("EventName", identity),
    "event_foreign_id": ("EventId", identity),
    "url": ("EventWebsite", identity),
    "start_date": ("EventDate", identity),
    "distances": ("Distances", distance_parser),
    "country": (None, identity),
    "city": ("City", identity),
    "state": ("State", identity),
    "latitude": ("Latitude", identity),
    "longitude": ("Longitude", identity),
    "virtual": ("VirtualEvent", identity)
}

UNMAPPED_DEFAULTS = {
    "country": "USA",
    "source_id": 1
}


class UltrasignupIngest(Ingest):

    def __init__(self):
        self.url = os.getenv("SOURCE_ULTRASIGNUP")
        if not self.url:
            raise ValueError("'SOURCE_ULTRASIGNUP' environment variable must be set")
        self.data = None
        self.parsed_data = None

    def fetch(self) -> None:
        params = {
            "virtual": 0,
            "open": 1,
            "past": 1,
            "lat": 30,
            "lng": -100,
            "mi": 50000,
            "mo": 12,
            "on": None,
            "m": [i for i in range(1, 13)],
            "c": [3, 4],
            "dist": 6
        }
        response = httpx.get(self.url, params=params)
        self.data = response.json()
        return

    def parse(self) -> None:
        if not self.data:
            raise Exception(
                "Please call '.fetch() before running .parse()")
        tmp_parsed_data = []
        for event in self.data:
            parsed_event = {}
            for key, value in SCHEMA_MAPPING.items():
                if value[0] is None:
                    # Not a mapped field:
                    parsed_event[key] = UNMAPPED_DEFAULTS[key]
                else:
                    # Remap the field:
                    parsed_event[key] = value[1](event[value[0]])
            tmp_parsed_data.append(parsed_event)
        self.parsed_data = tmp_parsed_data
        return

    # TODO:
    # event_foreign_id - not unique
    #
    # How to uniquely determine an event?
    # - Date must match
    # - City and State must match
    # - Name must match
    # - Distances - maybe separate table?

    def upload(self, client: Client):
        # Go event-by-event for now:
        for event in self.parsed_data:
            # Check if the event already exists
            echeck = client.table("events").select("id").match(
                {
                    "name": event["name"],
                    "start_date": event["start_date"],
                    "city": event["city"],
                    "state": event["state"]
                }
            ).execute()
            # If it does, then diff it, it has changes, then update
            if not len(echeck.data):
                # If it does not, then insert it
                log.info(
                    f"Event: {event['name']} in {event['city']}, "
                    f"{event['state']} on {event['start_date']} detected")
                out = client.table("events").insert(event).execute()
            else:
                # It already exists, pass for now, later check
                log.info(
                    f"Event: {event['name']} in {event['city']}, "
                    f"{event['state']} on {event['start_date']} already found")
            # Now, the event exists, time to process the distances:
            # First, get the event id:
            event_id_response = client.table("events").select("id").match(
                {
                    "name": event["name"],
                    "start_date": event["start_date"],
                    "city": event["city"],
                    "state": event["state"]
                }
            ).execute()
            event_id = event_id_response.data[0]["id"]
            for event_distance in event["distances"]:
                # Do we have this distance already?
                dist = distance_extract(event_distance)
                if dist is None:
                    log.info(f"Unable to process distance: {event_distance}")
                    continue
                else:
                    log.info(f"Parsed distance: {event_distance}")
                unit_id = client.table("distance_units").select("id").match({"unit_name": dist["unit"]}).execute()
                if not len(unit_id.data):
                    raise ValueError(f"Unknown unit: {dist['unit']}")
                unit_id = unit_id.data[0]["id"]
                # Query first to see if it exists
                distance_exists_query = client.table("event_distances").select("id").match({
                    "event_id": event_id,
                    "distance_unit_id": unit_id,
                    "distance": dist["length"]
                }).execute()
                distance_exists = len(distance_exists_query.data) > 0
                if not distance_exists:
                    # No, insert it:
                    out = client.table("event_distances").insert({
                        "event_id": event_id,
                        "distance": dist["length"],
                        "distance_unit_id": unit_id,
                        "is_relay": False,
                        "is_multiday": False,
                        "is_virtual": False
                    }).execute()
                    # Validate the insert
        return
