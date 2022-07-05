import copy
import logging as log
import os
import time
from typing import Dict, List, Optional

import httpx
from supabase import Client

from client import connect
from ingest.ingest import Ingest
from ingest.parser import distance_extract, identity
from ingest.ultrarequest import UltraRequest

from events import Event, EventList, event_list_dumps, event_list_loads


def not_on_site(x: str) -> bool:
    return x != "on_site"


def has_virtual_tag(x: Optional[List[str]]) -> bool:
    return "virtual" in x


def latlon_parser(x: Optional[Dict], ix: int) -> Optional[float]:
    try:
        return x["coordinates"][ix] if x else None
    except KeyError:
        return None


def lat_parser(x: Dict) -> Optional[float]:
    return latlon_parser(x, 1)


def lon_parser(x: Dict) -> Optional[float]:
    return latlon_parser(x, 0)


def activity_parser(x: List) -> Optional[List[str]]:
    unit_id_map = {
        1: "km",
        2: "meters",
        3: "miles",
        5: "hour"
    }
    if len(x) != 1:
        raise ValueError("Expected exactly one activity")
    unit_id = x[0]["distance_unit_id"]
    length = x[0]["distance"]
    # Meters to km conversion:
    if unit_id == 2:
        unit_id = 1
        length = length / 1000.0
    try:
        # Janky, but use for consistency
        return [f"{length} {unit_id_map[unit_id]}"]
    except KeyError:
        return None


def fetch_data(url, request_params, sleep=5) -> Dict:
    # Be polite:
    if sleep:
        time.sleep(sleep)
    return httpx.get(url, params=request_params).json()["races"]


def parse_data(batch):
    """
    Note that AhotuIngest() is not serializable, so we reinstantiate
    each time, instead of sending as an argument.

    :param batch:
    :return: Needs to be JSON, hence the event_list_dumps() call.
    """
    return event_list_dumps(AhotuIngest().parse(batch))


def upload_data(event_list):
    # Since tasks are run parallel potentially across different machines
    # we open new db connections for each, but control connections
    # via concurrency of the queue. For the fetch and parse tasks,
    # we have no restrictions on the queue concurrency.
    client = connect()
    return AhotuIngest().upload(
        event_list_loads(event_list), client=client)


class AhotuRequest(UltraRequest):

    def __init__(self, params: Dict):
        super().__init__(params)
        self.name = "Ahotu"
        self.url = os.getenv("SOURCE_AHOTU")
        if not self.url:
            raise ValueError(
                f"'SOURCE_{self.name.upper()}' environment variable must be set")
        self.params = params

    def fetch(self) -> Dict:
        """
        Later: return AhotuResponse. Error handling left to caller

        :return:
        """
        return fetch_data(url=self.url, request_params=self.params)


class AhotuIngest(Ingest):

    def __init__(self):
        super().__init__()
        self.name = "Ahotu"
        self.url = os.getenv("SOURCE_AHOTU")
        if not self.url:
            raise ValueError(
                f"'SOURCE_{self.name.upper()}' environment variable must be set")

        # Add these to the class to ensure caching:
        self.params = {
            "zoom": [68.0, 52.0, 1.2, -140.0],
            "language": "en",
            "activity": ["run"]
        }

        # Class constants:
        self.__schema_mapping = {
            "source_id": (None, identity),
            "name": ("event_name_en", identity),
            "event_foreign_id": ("id", identity),
            "url": ("registration_url", identity),
            "start_date": ("start_date", identity),
            "distances": ("activities", activity_parser),
            "country": ("country", identity),
            "city": ("city", identity),
            "state": (None, identity),  # could get this, do later
            "latitude": ("lonlat", lat_parser),
            "longitude": ("lonlat", lon_parser),
            "virtual": ("tags", has_virtual_tag)
        }
        self.__unmapped_defaults = {
            "country": None,
            "state": None,
            "source_id": 2
        }

    def fetch(self) -> List[AhotuRequest]:
        """
        :return:
        """
        # Need to get total number of pages:
        total_pages = httpx.get(
            self.url, params=self.params).json()["total_pages"]

        # Return a list of promises/functions that can be executed in parallel:
        request_list = []
        for page_ix in range(1, total_pages + 1):
            tmp_params = copy.deepcopy(self.params)
            tmp_params["page"] = page_ix
            request_list.append(AhotuRequest(params=tmp_params))
        return request_list

    def parse(self, batch: List[Dict]) -> EventList:
        log.info("Parsing events...")
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
        log.info(f"Successfully parsed {len(tmp_parsed_data)} events")
        return EventList([Event(**event) for event in tmp_parsed_data])

    def upload(self, parsed_batch: EventList, client: Client):
        # Go event-by-event for now:
        new_events = 0
        new_distances = 0
        for event in parsed_batch:
            # Check if the event already exists (event_foreign_id is not unique)
            # Skip virtual events for now as we need locations:
            if (event.city is None) and (event.country is None):
                log.info("Skipping locationless event...")
                continue
            event_distances = event.distances

            # Query for the event distances at the same time, to avoid multiple db queries:
            echeck = client.table("events").select("id").match(
                {
                    "name": event.name,
                    "start_date": event.start_date,
                    "city": event.city,
                    "country": event.country
                }
            ).execute()

            # If it does, then diff it, it has changes, then update
            if not len(echeck.data):
                # If it does not, then insert it
                log.info(
                    f"Event: {event.name} in {event.city}, "
                    f"{event.country} on {event.start_date} detected")
                out = client.table("events").insert(event.todict(schema=True)).execute()
                new_events += 1
                # Can we get the id of the inserted event?
                # event_id = out.data[0]["id"]
            else:
                # It already exists, pass for now, later check
                log.info(
                    f"Event: {event.name} in {event.city}, "
                    f"{event.country} on {event.start_date} already found")

            # Now, the event exists, time to process the distances:
            # First, get the event id:
            # We should already have this... remove it later:
            event_id_response = client.table("events").select("id").match(
                {
                    "name": event.name,
                    "start_date": event.start_date,
                    "city": event.city,
                    "country": event.country
                }
            ).execute()
            event_id = event_id_response.data[0]["id"]

            # Each distance is a separate event
            # Skip if null:
            if event_distances is None:
                continue
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
            # End of event distances handling, loop has been continued
            # to the next event so no additional handling should be done
        # Summarize:
        log.info(f"Inserted {new_events} new events")
        log.info(f"Inserted {new_distances} new distances")
        return
