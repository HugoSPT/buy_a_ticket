from datetime import datetime
import json
from json.decoder import JSONDecodeError
from mongoengine.errors import OperationError

from django.conf import settings
from django.http import JsonResponse
from django.views.generic import View

from api.models import Venue
from api.exceptions import NotFoundException


class VenuesView(View):
    def get(self, request, page):
        items_per_page = 10
        venues = Venue.objects.skip((int(page) - 1) * items_per_page).limit(items_per_page)

        return JsonResponse({'venues': [venue.to_dict() for venue in venues]})


class VenueView(View):
    def get(self, request, venue_id):
        exclude = []

        if not request.GET.get('events', False):
            exclude.append('events')

        if not request.GET.get('layout', False):
            exclude.append('base_layout')

        try:
            venue = Venue.objects(id=venue_id).exclude(*exclude)[0]
        except IndexError:
            return JsonResponse({'error': f'Venue with id {venue_id} not found'}, status=404)

        return JsonResponse({'venue': venue.to_dict()})

    def post(self, request):
        try:
            data = json.loads(request.body)
            venue_name = data['venue_name']
        except (JSONDecodeError, KeyError):
            return JsonResponse({'error': 'Malformed JSON or missing field'}, status=400)

        if Venue.objects(venue_name=venue_name):
            return JsonResponse({'error': 'A venue with the same name already exists'}, status=409)

        try:
            venue = Venue(venue_name=venue_name, input_json=data)
            venue.create_venue(data['sections'])
        except OperationError:
            return JsonResponse({'error': 'Something went wrong saving the venue'}, status=500)

        return JsonResponse({'venue': venue.to_dict()})


class VenueEventView(View):
    def get(self, request, venue_id, event_id):
        try:
            event = Venue.objects(id=venue_id)[0].get_event(event_id=event_id)
        except IndexError:
            return JsonResponse({'error': f'Venue with id {venue_id} not found'}, status=404)
        except NotFoundException:
            return JsonResponse({'error': f'Event with id {event_id} not found'}, status=404)

        return JsonResponse({'event': event.to_dict()})

    def post(self, request, venue_id):
        try:
            data = json.loads(request.body)
            event_name = data['event_name']
            date = datetime.strptime(data['date'], settings.DATE_FMT)
        except JSONDecodeError:
            return JsonResponse({'error': 'Malformed JSON'}, status=400)

        try:
            venue = Venue.objects(id=venue_id)[0]
        except IndexError:
            return JsonResponse({'error': f'Venue with id {venue_id} not found'}, status=404)

        try:
            event = venue.create_event(date=date, event_name=event_name)
        except OperationError:
            return JsonResponse({'error': 'Something went wrong creating the event'}, status=500)

        return JsonResponse({'event': event.to_dict()})


class VenueEventReservationView(View):
    def post(self, request, venue_id, event_id):
        try:
            data = json.loads(request.body)
            group = [int(element) for element in list(data['group'])]
            section = data['section']
        except (JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Malformed JSON'}, status=400)

        try:
            result = Venue.objects(id=venue_id)[0].make_reservation(event_id, section, group)
        except IndexError:
            return JsonResponse({'error': f'Venue with id {venue_id} not found'}, status=404)
        except NotFoundException:
            return JsonResponse({'error': f'Event with id {event_id} not found'}, status=404)

        if all([True if num_people == 0 else False for num_people in result]):
            return JsonResponse({})

        return JsonResponse({'error': f'Couldn\'t seat all people. Missing space for {result}'}, status=403)


class VenueEventBlockView(View):
    def post(self, request, venue_id, event_id):
        try:
            data = json.loads(request.body)
            section = data['section']
            row_id = data['row_id']
            seat_id = data['seat_id']
        except (JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Malformed JSON'}, status=400)

        try:
            result = Venue.objects(id=venue_id)[0].block(event_id, section, row_id, seat_id)
        except IndexError:
            return JsonResponse({'error': f'Venue with id {venue_id} not found'}, status=404)
        except NotFoundException:
            return JsonResponse({'error': f'Event with id {event_id} not found'}, status=404)

        response, status = ({}, 200) if result \
            else ({'error': f'Couldn\'t block the seat because it is not free.'}, 403)

        return JsonResponse(response, status=status)
