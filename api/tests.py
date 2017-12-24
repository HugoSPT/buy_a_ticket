import copy
from datetime import datetime
import django
import json
import time
import unittest

from django.conf import settings
from django.test import Client

from api.models import Venue

django.setup()

VENUE = {
  "venue_name": "Testing Venue",
  "sections": [
    {
      "section_type": "house",
      "rows": [
        {
          "row_rank": "1st Rank",
          "num_seats": 8,
          "num_rows": 3,
          "order": "non-sequential"
        }
      ]
    }
  ]
}

EVENT = {
  "event_name": "Event Testing",
  "date": "01-01-2017T12:00:00"
}


class TestVenueView(unittest.TestCase):

    def setUp(self):
        self.client = Client()
        self.venue = Venue(venue_name=VENUE['venue_name'], input_json=VENUE)
        self.venue.create_venue(VENUE['sections'])

    def test_get_venue_error(self):
        res = self.client.get(f'/api/1.0/venue/this-id-doesnt-exist')

        self.assertEquals(res.status_code, 404)

    def test_get_venue_no_get_arguments(self):
        res = self.client.get(f'/api/1.0/venue/{self.venue.id}')

        self.assertEqual(res.status_code, 200)

        venue = res.json()['venue']

        self.assertEqual(venue['venue_name'], self.venue['venue_name'])
        self.assertEqual(venue['base_layout'], {})

    def test_get_venue_get_arguments(self):
        res = self.client.get(f'/api/1.0/venue/{self.venue.id}?layout=True')

        self.assertEqual(res.status_code, 200)

        venue = res.json()['venue']

        self.assertEqual(venue['venue_name'], self.venue['venue_name'])
        self.assertTrue(VENUE['sections'][0]['section_type'] in venue['base_layout'])

    def test_post_venue_malformed_json(self):
        res = self.client.post(f'/api/1.0/venue/', VENUE, content_type="application/json")
        self.assertEquals(res.status_code, 400)

    def test_post_venue_existing_venue(self):
        res = self.client.post(f'/api/1.0/venue/', json.dumps(VENUE), content_type="application/json")
        self.assertEquals(res.status_code, 409)

    def test_post_venue(self):
        new_venue = copy.deepcopy(VENUE)
        new_venue['venue_name'] = f'New Name-{time.gmtime()}'

        res = self.client.post(f'/api/1.0/venue/', json.dumps(new_venue), content_type="application/json")

        self.assertEquals(res.status_code, 200)

        venue = res.json()['venue']

        self.assertEquals(venue['venue_name'], new_venue['venue_name'])


class TestVenueEventView(unittest.TestCase):

    def setUp(self):
        self.client = Client()
        self.venue = Venue(venue_name=VENUE['venue_name'], input_json=VENUE)
        self.venue.create_venue(VENUE['sections'])
        self.event = self.venue.create_event(date=datetime.strptime(EVENT['date'], settings.DATE_FMT))

    def test_get_venue_event(self):
        res = self.client.get(f'/api/1.0/venue/{self.venue.id}/event/{self.event.id}/')

        self.assertEquals(res.status_code, 200)

        event = res.json()['event']

        self.assertEquals(event['event_name'], self.event.event_name)

    def test_post_venue_event(self):
        new_event = copy.deepcopy(EVENT)
        new_event['event_name'] = f'New Event-{time.gmtime()}'

        res = self.client.post(
            f'/api/1.0/venue/{self.venue.id}/event/',
            json.dumps(new_event), content_type="application/json"
        )

        self.assertEquals(res.status_code, 200)

        event = res.json()['event']

        self.assertEquals(event['event_name'], new_event['event_name'])
