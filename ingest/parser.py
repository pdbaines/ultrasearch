from typing import List, Optional, TypedDict
import re

rcl = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)")
rcu = re.compile(r"\D+")


class UnitError(ValueError):
    pass


class UnitValuePair(TypedDict):
    length: float
    unit: str


def identity(x):
    return x


def distance_parser(x: str) -> List:
    return [elt.lstrip().rstrip() for elt in x.split(",")]


def remap(x: str) -> str:
    """ Map a string to a valid unit.

    str x: The string to map.
    :return: The mapped string. Valid options are:
        ``mile``, ``km`` and ``hour``.
    """
    if x in ["miler", "mile", "m", "mi", "miles", "m run", "mile run"]:
        return "mile"
    if x in ["k", "km", "kms", "kilometers", "kilometer", "k run", "km run"]:
        return "km"
    if x in ["hour", "hrs", "hr", "hr run", "hour run", "hour night run", "hour day run"]:
        return "hour"
    raise UnitError(f"Unknown unit: {x}")


def distance_extract(x: str) -> Optional[UnitValuePair]:
    """
    Extract the distance and unit from a string.

    :param x: the input string
    :return: The length and unit pair, or None
    """
    x = x.lstrip().rstrip().lower()
    if x == "marathon":
        return {"length": 26.2, "unit": "mile"}
    if x in ["half marathon", "1/2 marathon"]:
        return {"length": 13.1, "unit": "mile"}
    if x in ["mile", "beer mile"]:
        return {"length": 1.0, "unit": "mile"}
    if x in ["kilometer", "beer kilometer"]:
        return {"length": 1.0, "unit": "km"}
    # Extract length and units:
    lgroups = rcl.findall(x)
    ugroups = rcu.findall(x)
    unit = length = None
    for group in ugroups:
        if group in [".", ""]:
            continue
        unit = group
    if unit is None:
        return
    if not len(lgroups):
        return
    for group in lgroups:
        length = group
    # Convert:
    length = float(length)
    # Check:
    try:
        unit = remap(unit.lower().lstrip().rstrip())
        return {"length": length, "unit": unit}
    except UnitError:
        return
