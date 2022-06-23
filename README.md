## Local Development

```commandline
conda activate ultrasearch

brew install supabase/tap/supabase

supabase init   # only needed once
supbase start   # start supbase locally

psql 'postgresql://postgres:postgres@localhost:54322/postgres'
```

## Containerized Development

```yaml
make build
```

## API Exploration

### Ultrasignup

API overview:
```
# Endpoint for converting zipcodes to co-ordinates (not needed):
curl -X POST -H "Content-Type: application/json" -d '{"search":"91101"}' https://ultrasignup.com/service/events.svc/location/search

# Get events list:
curl "https://ultrasignup.com/service/events.svc/closestevents?virtual=0&open=1&past=1&lat=30&lng=-100&mi=500&mo=12&on&m=1,2,3,4,5,6,7,8,9,10,11,12&c=3,4&dist=6"
```
Example output:
```
{
     "BannerId": "a6cd09c7-5dfc-49c4-aa9b-1003826b0d5b",
     "Cancelled": false,
     "City": "Smithfield",
     "DistanceCategories": " non ultra",
     "Distances": "10hrs, 10 Hour TEAM, Ruck -10 Hours, Ruck -5 Hours, Half Windsor (5hour), 3 Miler, Ruck -2 Hours,",
     "EventDate": "6/10/2023",
     "EventDateEnd": null,
     "EventDateId": 48909,
     "EventDateOriginal": "6/10/2023",
     "EventDistances": null,
     "EventId": 13550,
     "EventImages": [
       {
         "ImageId": "b2369642-9865-4474-95d1-238fab963295",
         "ImageLabel": null
       }
     ],
     "EventName": "Windsor Castle 10-Hour",
     "EventType": 0,
     "EventWebsite": "",
     "GroupId": 0,
     "GroupName": null,
     "Latitude": "36.9759",
     "Location": "",
     "Longitude": "-76.6261",
     "Postponed": false,
     "State": "VA",
     "VirtualEvent": false
   }
```

#
# Ingest adapters from sources
# Ingest runs on schedule
# Ingested to database (supabase)
# Searchable layer on database
# Ingest adds new row when changes are detected
# Prior versions are retained for posterity

# Ultrasignup
# MarathonGuide.com
# runningintheusa
# https://utmb.world/utmb-world-series-events
# curl "https://www.ahotu.com/advanced-search.json?language=en&zoom[]=68.78414378041504&zoom[]=52.3828125&zoom[]=1.2303741774326145&zoom[]=-139.92187500000003&activity[]=run&page=22"

#
#
# Parsed:
# - id
# - source
# - EventName
# - EventType
# - EventWebsite
# - EventImages
# - EventDate
# - EventDateEnd
# - EventDateOriginal
# - EventDistances
# - Cancelled
# - Postponed
# - Location
# - City
# - State
# - Latitude
# - Longitude
# - VirtualEvent
# -
