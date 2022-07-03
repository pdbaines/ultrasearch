
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
        return self.__dict__["city"]

    @property
    def country(self):
        return self.__dict__["country"]

    @property
    def state(self):
        return self.__dict__["state"]

    @property
    def start_date(self):
        return self.__dict__["start_date"]

    @property
    def name(self):
        return self.__dict__["name"]

    @property
    def distances(self):
        return self.__dict__["distances"]

    def todict(self, schema: bool = False):
        return self.__dict__ if not schema else {k: v for k, v in self.__dict__.items() if k in self.__schema}
