import json

from events import Event, EventList, event_dumps, event_loads, event_list_dumps, event_list_loads


j1 = {
    "city": "New York",
    "country": "USA",
    "state": "NY",
    "start_date": "2020-01-01",
    "name": "Event 1",
    "latitude": 90,
    "longitude": -180
}

j2 = {
    "city": "San Francisco",
    "country": "USA",
    "state": "CA",
    "start_date": "2021-01-01",
    "name": "Event 2",
    "latitude": None,
    "longitude": None
}


def test_event_list():
    e1 = Event(**j1)
    e2 = Event(**j2)
    el1 = EventList([e1, e2])
    assert len(el1) == 2


def test_event_list_dumps():
    e1 = Event(**j1)
    e2 = Event(**j2)
    el1 = EventList([e1, e2])
    assert event_list_dumps(el1) == '[' + event_dumps(e1) + ', ' + event_dumps(e2) + ']'


def test_event_dumps():
    e1 = Event(**j1)
    assert event_dumps(e1) == json.dumps(e1.__dict__)


def test_event_round_trip():
    e1 = Event(**j1)
    e2 = event_loads(event_dumps(e1))
    assert e1 == e2


def test_event_list_round_trip():
    e1 = Event(**j1)
    e2 = Event(**j2)
    el1 = EventList([e1, e2])
    el2 = event_list_loads(event_list_dumps(el1))
    assert el1 == el2


def test_event_list_iterable():
    e1 = Event(**j1)
    e2 = Event(**j2)
    el1 = EventList([e1, e2])
    for e in el1:
        assert e in el1
