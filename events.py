import json
from json import JSONEncoder
from typing import List


class Event:

    def __init__(self, **params):
        # Columns to present in public schema:
        self.__schema = [
            "source_id",
            "name",
            "start_date",
            "city",
            "state",
            "country",
            "url",
            "virtual",
            "latitude",
            "longitude"
        ]
        self.__dict__.update(params)

        # Validation:
        self.latitude = float(self.latitude) if (self.latitude is not None) else None
        self.longitude = float(self.longitude) if (self.longitude is not None) else None
        if self.latitude is not None:
            if self.latitude < -90 or self.latitude > 90:
                self.__dict__["latitude"] = self.__dict__["latitude"] % 90
        if self.longitude is not None:
            if self.longitude < -180 or self.longitude > 180:
                self.__dict__["longitude"] = self.__dict__["longitude"] % 180

    @property
    def city(self):
        return self.__dict__.get("city")

    @property
    def country(self):
        return self.__dict__.get("country")

    @property
    def state(self):
        return self.__dict__.get("state")

    @property
    def start_date(self):
        return self.__dict__.get("start_date")

    @property
    def name(self):
        return self.__dict__.get("name")

    @property
    def distances(self):
        return self.__dict__.get("distances")

    @property
    def latitude(self):
        return self.__dict__.get("latitude")

    @property
    def longitude(self):
        return self.__dict__.get("longitude")

    @latitude.setter
    def latitude(self, latitude):
        self.__dict__["latitude"] = latitude

    @longitude.setter
    def longitude(self, longitude):
        self.__dict__["longitude"] = longitude

    def todict(self, schema: bool = False):
        return self.__dict__ if not schema else {k: v for k, v in self.__dict__.items() if k in self.__schema}

    def __eq__(self, other):
        if not isinstance(other, Event):
            return False
        return self.__dict__ == other.__dict__


class EventList:

    def __init__(self, events: List[Event]):
        self.events = events

    def __get__(self, i):
        return self.events[i]

    def __getitem__(self, i):
        return self.events[i]

    def __len__(self):
        return len(self.events)

    def __eq__(self, other):
        if not isinstance(other, EventList):
            return False
        return self.events == other.events


class EventEncoder(JSONEncoder):

    def default(self, o):
        return o.__dict__


class EventListEncoder(JSONEncoder):

    def default(self, o):
        if not isinstance(o, EventList):
            raise TypeError((
                f"EventListEncoder can only encode EventList objects "
                f"(received: {type(o)})"))
        return [event.__dict__ for event in o.events]


def event_dumps(obj):
    return json.dumps(obj, cls=EventEncoder)


def event_list_dumps(obj):
    return json.dumps(obj, cls=EventListEncoder)


def event_loads(out):
    return Event(**json.loads(out))


def _event_list_loader(out):
    return EventList([Event(**event) for event in out])


def event_list_loads(out):
    return _event_list_loader(json.loads(out))


def celery_event_list_loads(out):
    return _event_list_loader(json.loads(out)[0][0])
