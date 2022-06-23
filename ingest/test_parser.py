from parser import distance_extract


def test_distance_extract():
    assert distance_extract("13.1 Miler") == {"unit": "mile", "length": 13.1}
    assert distance_extract("200 Miler") == {"unit": "mile", "length": 200}
    assert distance_extract("200.1 Miler") == {"unit": "mile", "length": 200.1}
    assert distance_extract("200M") == {"unit": "mile", "length": 200}
    assert distance_extract("200.1Mi") == {"unit": "mile", "length": 200.1}
    assert distance_extract("200 Miles") == {"unit": "mile", "length": 200}
    assert distance_extract("200.1 miles") == {"unit": "mile", "length": 200.1}
    assert distance_extract("100M RUN") == {"unit": "mile", "length": 100}

    assert distance_extract("13.1 KM") == {"unit": "km", "length": 13.1}
    assert distance_extract("200KM") == {"unit": "km", "length": 200}
    assert distance_extract("200.1KM") == {"unit": "km", "length": 200.1}
    assert distance_extract("200K") == {"unit": "km", "length": 200}
    assert distance_extract("200.1 K") == {"unit": "km", "length": 200.1}
    assert distance_extract("200 Kilometer") == {"unit": "km", "length": 200}
    assert distance_extract("200.1 kilometers") == {"unit": "km", "length": 200.1}
    assert distance_extract("200.1 K") == {"unit": "km", "length": 200.1}
    assert distance_extract("55.5K RUN") == {"unit": "km", "length": 55.5}
    assert distance_extract("55K RUN") == {"unit": "km", "length": 55}

def test_time_extract():
    assert distance_extract("24hrs") == {"unit": "hour", "length": 24}
    assert distance_extract("24.1hr") == {"unit": "hour", "length": 24.1}
    assert distance_extract("24 HR") == {"unit": "hour", "length": 24}
    assert distance_extract("2 hour") == {"unit": "hour", "length": 2}
    #assert distance_extract("12 hour 9AM") == {"unit": "hour", "length": 12}
    #assert distance_extract("12 hour 9 AM") == {"unit": "hour", "length": 12}
    assert distance_extract("12 hour run") == {"unit": "hour", "length": 12}
    assert distance_extract("12 hour night run") == {"unit": "hour", "length": 12}


def test_special():
    assert distance_extract("marathon") == {"unit": "mile", "length": 26.2}
    assert distance_extract("half marathon") == {"unit": "mile", "length": 13.1}
    assert distance_extract("1/2 marathon") == {"unit": "mile", "length": 13.1}


# 55k run
# 100-mile Solo Event
# 99-mile Relay Event
# 100 Mile - 5 Person Relay
# 24hrs
# 2 hour
# 24 hours
# 12hr night run
# 12hr 9 AM
# 12hr 9AM
# 12hr 11 PM
# 25 K - Virtual