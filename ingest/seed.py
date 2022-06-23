# Idempotent seeding file for database components
from client import connect


def seed_distance_units():
    client = connect()
    client.table("distance_units").upsert({"id": 1, "unit_name": "mile", "unit_type": "distance", "unit_to_km": 1.609344}).execute()
    client.table("distance_units").upsert({"id": 2, "unit_name": "km", "unit_type": "distance", "unit_to_km": 1.0}).execute()
    client.table("distance_units").upsert({"id": 3, "unit_name": "hour", "unit_type": "time"}).execute()
    return

def seed_sources():
    client = connect()
    client.table("sources").upsert({"id": 1, "name": "UltraSignup", "base_url": "ultrasignup.com"}).execute()
    client.table("sources").upsert({"id": 2, "name": "Ahotu", "base_url": "ahotu.com"}).execute()
    return

if __name__ == "__main__":
    seed_distance_units()
    seed_sources()