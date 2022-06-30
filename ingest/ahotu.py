import copy
import logging as log
import os
import time
from typing import Dict, List, Optional

import httpx
from supabase import Client

from ingest.ingest import Ingest
from ingest.parser import distance_extract, identity

from events import Event

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


def activity_parser(x: List) -> Optional[Dict]:
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


class AhotuIngest(Ingest):

    def __init__(self):
        self.name = "Ahotu"
        self.url = os.getenv("SOURCE_AHOTU")
        if not self.url:
            raise ValueError(
                f"'SOURCE_{self.name.upper()}' environment variable must be set")
        self.data = None
        self.parsed_data = None

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

    def fetch(self, interval=1, max_pages=None) -> List[Dict]:
        """
        TODO: Return iterable for batching fetch, parse, upload
        TODO: Cache each fetch to blob storage

        :return:
        """
        params = {
            "zoom": [68.0, 52.0, 1.2, -140.0],
            "language": "en",
            "activity": ["run"]
        }
        # API response schema:
        # {
        #   "races": [<race>],
        #   "total": <int>,
        #   "pages": <int>,
        #   "total_pages": <int>
        # }
        # where <race>:
        # {
        #    "@search.score": <float>,
        #    "id": <str>,
        # 	 "past_future": <int>,
        # 	 "race_name": <str>,
        # 	 "event_name_en": <str>,
        # 	 "event_name_fr": <str>,
        # 	 "event_id": <int>,
        # 	 "edition_id": <int>,
        # 	 "edition_date": <timestamp>,
        # 	 "permalink": <str>,
        # 	 "edition_status": <int>,
        # 	 "event_status": <int>,
        # 	 "date_status": null,
        # 	 "start_date": "2022-06-30T00:00:00Z",
        # 	 "start_time": "08:00",
        # 	 "end_date": null,
        # 	 "months": [<int>],
        # 	 "tags": [<str>],
        # 	 "lonlat": {
        # 		"type": "Point",
        # 		"coordinates": [
        # 			0.583534800000052,
        # 			52.2412949
        # 		],
        # 		"crs": {
        # 			"type": "name",
        # 			"properties": {
        # 				"name": "EPSG:4326"
        # 			}
        # 		}
        # 	 },
        # 	 "city": <str>,
        # 	 "country": <str>,
        # 	 "continent": <int>,
        # 	 "sub_continent": 154,
        # 	 "region_1": 239,
        # 	 "region_2": 402,
        # 	 "location_en": "Europe / Northern Europe / United Kingdom / England / Suffolk / Bury St Edmunds",
        # 	 "location_fr": "Europe / Europe du Nord / Royaume-Uni / Angleterre / Suffolk / Bury St Edmunds",
        # 	 "activity": "run",
        # 	 "race_type": 1,
        # 	 "registration_affiliation": null,
        # 	 "registration_affiliation_data": null,
        # 	 "registration_starts_on": null,
        # 	 "registration_ends_on": "2022-06-22T00:00:00Z",
        # 	 "field_size": "",
        # 	 "venue": "on_site",
        # 	 "distance_km": 42.195,
        # 	 "minutes": null,
        # 	 "registration_url": "https://www.suffolkrunningcentre.co.uk/product-page/summer-10-in-10",
        # 	 "time_zone_offset_to_local": 0,
        # 	 "time_zone_offset_id": "United Kingdom Time",
        # 	 "current_edition": true,
        # 	 "featured": false,
        # 	 "activities": [
        # 		{
        # 			"activity": "run",
        # 			"order": 1,
        # 			"distance": 42.195,
        # 			"distance_unit_id": 1,
        # 			"distance_km": 42.195,
        # 			"tags": [
        # 				"multi_terrain"
        # 			],
        # 			"elevation_gain": null,
        # 			"elevation_gain_unit_id": null,
        # 			"elevation_gain_m": null
        # 		}
        # 	 ],
        # 	 "registration_open": false,
        # 	 "registration_category": "none"
        # }

        # API has pagination :)

        # TODO: timeouts and retries:
        try:
            response = httpx.get(self.url, params=params)
        except Exception as e:
            log.info(f"Failed to fetch data from {self.url}")
            raise e

        tmp = response.json()
        event_ctr = 0
        total_pages = tmp["total_pages"]
        max_pages_bound = \
            total_pages + 1 if max_pages is None else \
                min(max_pages + 1, total_pages + 1)
        for page in range(1, max_pages_bound):
            # Note, we re-query the first page, but meh:
            log.info(f"Fetching page {page}/{total_pages}...")
            tmp_params = copy.deepcopy(params)
            params["page"] = page
            response = httpx.get(self.url, params=tmp_params)
            if interval:
                time.sleep(interval)
            tmp_events = response.json()["races"]
            event_ctr += len(tmp_events)
            yield tmp_events

        log.info(f"Fetched {event_ctr} events")
        return

    def parse(self, batch: List[Dict]) -> List[Event]:
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
        return [Event(**event) for event in tmp_parsed_data]

    def upload(self, parsed_batch: List[Event], client: Client):
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
            else:
                # It already exists, pass for now, later check
                log.info(
                    f"Event: {event.name} in {event.city}, "
                    f"{event.country} on {event.start_date} already found")
            # Now, the event exists, time to process the distances:
            # First, get the event id:
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
