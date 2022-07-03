import copy
import logging as log
import os
import time
from typing import List, Dict

import httpx
from supabase import Client

from events import Event
from ingest.ultrarequest import UltraRequest
from ingest.ingest import Ingest
from ingest.parser import distance_parser, distance_extract, identity


class UltrasignupRequest(UltraRequest):

    def __init__(self, params: Dict):
        self.name = "Ultrasignup"
        self.url = os.getenv("SOURCE_ULTRASIGNUP")
        if not self.url:
            raise ValueError("'SOURCE_ULTRASIGNUP' environment variable must be set")
        self.params = params

    def fetch(self) -> Dict:
        """
        Later: return UltrasignupResponse. Error handling left to caller

        :return:
        """
        return fetch_data(self.url, self.params)


def fetch_data(url, request_params) -> Dict:
    tmp = httpx.get(url, params=request_params).json()
    if len(tmp) == 100:
        raise InternalError(
            f"Ultrasignup API returned more than 100 events for "
            "month {month} and distance {dist}")
    return tmp


class UltrasignupIngest(Ingest):

    def __init__(self):
        self.url = os.getenv("SOURCE_ULTRASIGNUP")
        if not self.url:
            raise ValueError("'SOURCE_ULTRASIGNUP' environment variable must be set")

        # Class constants:
        self.__unmapped_defaults = {
            "country": "USA",
            "source_id": 1
        }
        self.__schema_mapping = {
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

    def fetch(self) -> List[UltrasignupRequest]:
        """

        :return:
        """
        params = {
            "virtual": 0,
            "lat": 30,
            "lng": -100,
            "mi": 50000,
            "m": [i for i in range(11, 13)],
            "dist": [i for i in range(6, 9)]
        }
        # API only returns max 100 with no pagination :(
        # Iterate over months and distance pairs:
        request_list = []
        for month in params["m"]:
            for dist in params["dist"]:
                log.info(f"Fetching month {month} and distance {dist}...")
                tmp_params = copy.deepcopy(params)
                tmp_params["m"] = month
                tmp_params["dist"] = dist
                request_list.append(UltrasignupRequest(tmp_params))
        return request_list

    def parse(self, batch: List[Dict]) -> List[Event]:
        tmp_parsed_data = []
        for event in batch:
            parsed_event = {}
            for key, value in self.__schema_mapping.items():
                if value[0] is None:
                    # Not a mapped field:
                    parsed_event[key] = self.__unmapped_defaults[key]
                else:
                    # Remap the field:
                    parsed_event[key] = value[1](event[value[0]])
            tmp_parsed_data.append(parsed_event)
        return [Event(**tmp_event) for tmp_event in tmp_parsed_data]

    def upload(self, parsed_batch: List[Event], client: Client):
        # Go event-by-event for now:
        new_events = 0
        new_distances = 0
        for event in parsed_batch:
            # Check if the event already exists (event_foreign_id is not unique)
            event_distances = event.distances
            echeck = client.table("events").select("id").match(
                {
                    "name": event.name,
                    "start_date": event.start_date,
                    "city": event.city,
                    "state": event.state
                }
            ).execute()
            # If it does, then diff it, it has changes, then update
            if not len(echeck.data):
                # If it does not, then insert it
                log.info(
                    f"Event: {event.name} in {event.city}, "
                    f"{event.state} on {event.start_date} detected")
                out = client.table("events").insert(event.todict(schema=True)).execute()
                new_events += 1
            else:
                # It already exists, pass for now, later check
                log.info(
                    f"Event: {event.name} in {event.city}, "
                    f"{event.state} on {event.start_date} already found")
            # Now, the event exists, time to process the distances:
            # First, get the event id:
            event_id_response = client.table("events").select("id").match(
                {
                    "name": event.name,
                    "start_date": event.start_date,
                    "city": event.city,
                    "state": event.state
                }
            ).execute()
            event_id = event_id_response.data[0]["id"]
            for event_distance in event_distances:
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
                    new_distances += 1
                    # Validate the insert
        # Summarize:
        log.info(f"Inserted {new_events} new events")
        log.info(f"Inserted {new_distances} new distances")
        return
