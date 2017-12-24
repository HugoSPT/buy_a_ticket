# Work done
API: `http://54.226.83.223:8000/api/v1.0/ip/28.180.236.152`. But README first please.

## System Description
This project implements a very simple event reservation system where people can buy tickets for
different sections of the venue.

All the project was developed using Python and Django web framework.

### Requirements
Python 3.6.2 (this is important due the new dict implementation and f strings)
MongoDB


### API
The API provides an endpoint to get an IP's info.

The root endpoint is `/api/v1.0/ip/<ip_address>`. The use of `/v1.0/` is useful for versioning and keeping backwards
compatibility. We can develop a new version of the API (let's say `2.0`) without changing anything from the version
`1.0`, keeping the clients unchanged.


## Installation
These are the steps to setup the local environment to both run the importer and the API.

1. Install MongoDB;

2. Install `requirements.txt` in root directory (`pip install -r requirements.txt`)

3. Export Django's settings module `export DJANGO_SETTINGS_MODULE=buy_a_ticket.settings`
(in the case you want to run tests)


And you should be ready to start!


## How to run it

### API
To run the API just type `python manage.py runserver` and you are ready to make requests against it.


## Endpoints

The API expose 5 endpoints.

### `GET /api/1.0/venues/<page>/`

Lists all venues (10 per page)

### `GET /api/1.0/venue/<venue_id>/`

Show `<venue_id>` venue info

### `POST /api/1.0/venue/`

creates a new venue providing a JSON in the request. The JSON has the following format:

```
{
  "venue_name": "Venue Name",
  "sections": [
    {
      "section_type": "house",
      "rows": [
        {
          "row_rank": "1st Rank",
          "num_seats": 8,
          "num_rows": 3,
          "order": "non-sequential"
        },
        {
          "row_rank": "1st Rank",
          "num_seats": 9,
          "num_rows": 3,
          "order": "non-sequential"
        },
        {
          "row_rank": "2nd Rank",
          "num_seats": 12,
          "num_rows": 2,
          "order": "sequential"
        },
        {
          "row_rank": "3rd Rank",
          "num_seats": 10,
          "num_rows": 1,
          "order": "sequential"
        }
      ]
    },
    {
      "section_type": "box",
      "rows": [
        {
          "row_rank": "1st Rank",
          "num_seats": 10,
          "num_rows": 2,
          "order": "sequential"

        }
      ]
    }
  ]
}
```

The JSON above will create a venue called `Venue Name` with two sections, `house` and `box`.

Section `house` has 9 rows, 6 in 1st Rank, 2 in 2nd Rank and 1 in 3rd Rank. The seats in 1st Rank rows are
non-sequential` ordered (1 3 5 6 4 2) and the sests in 2nd and 3rd rows are `sequential`ordered (1 2 3 4...).

### `GET /api/1.0/venue/<venue_id>/event/<event_id>/`

Return `<event_id>` event info happening in `<venue_id>` venue.

### `POST /api/1.0/venue/<venue_id>/event/`

Creates an event in venue `<venue_id>`. Reservations are made in events and it expects the following JSON.

```
{
  "event_name": "Event Testing",
  "date": "01-01-2017T12:00:00"
}
```

This will create an event with name `Event Testing` happening on the January 1st 2017 at midday.

### `POST /api/1.0/venue/<venue_id>/event/<event_id>/reserve/`

Makes a reservation in `<event_id>` event happening on `<venue_id>` venue.

It expects the following JSON to be sent in the request.

```
{
  "section": "house",
  "group": [10, 3, 2]
}
```

This will seat 10 people in 1st Rank on section `house`, 3 people in 2nd Rank and 2 in 3rd Rank.

### POST /api/1.0/venue/<venue_id>/event/<event_id>/block/

Blocks a seat due technical reasons * if the seat is free *.

The following JSON should be provided.

```
{
  "section": "house",
  "row_id": 2,
  "seat_id": 3
}
```

This input will block the seat with id 3 located in row 2 in section `house`.

## Web

You can see the reservation status of an event in your browser going to:
`/venue/<venue_id>/event/<event_id>/`


## Algorithm

The reservation algorithm is based on the empty seats each row in each section that are still available.

Before making a reservation, the algo will generate a structure `availability` containing all seats with a
given N contagious seats.

```
{
    "1st Rank": {
        "1": {
            "1": [1],
            "2": [2, 3, 9, 10]
            "3": [5, 6, 7],
            "4": [12, 13, 14, 15]
        },
        "2": {
            ...
        }
    }
}
```

This structure tells us that if people want to seat in 1st Rank rows, row 1 has 1 isolated seat (seat with id 1),
2 2-contiguous seats (2, 3 and 9, 10) and 1 3-contiguous seats (5, 6, 7) and 1 4-contiguous seats (12, 13, 14, 15).

By building this structure we can easily do all the efforts to seat the group of people together. If we want to seat a group
of 3 people, it will search if there is any 3-contiguous seats in the structure; if so (in the case above),
it will seat the people in there. Now, let's imagine there is no 3-contiguous seats - it will search in bigger number
of available seats (in this case 4). If there is no way to seat the people together, the algo will try to sit them on
2-contiguous seats or isolated seats.

## Improvements
* Keeping the `availability` structure cached would be a huge improvement since we didn't need to generate it
in every reservation. But then a synchronization problem needs to be solved due multiple processes/nodes accessing
the same data.
* I've done the minimum unit test possible due lack of time. In a "real case" I would make tests for almost every
function both in API endpoints and models.

Looking forward for your feedback!
