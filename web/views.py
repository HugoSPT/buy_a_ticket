import requests

from django.conf import settings
from django.views import generic


class TemplateView(generic.TemplateView):
    def __init__(self, *args, **kwargs):
        self.context = {}
        super(TemplateView, self).__init__(*args, **kwargs)


class VenueEventView(TemplateView):
    template_name = "event.html"

    def get(self, request, venue_id, event_id, *args, **kwargs):
        response = requests.get(f'{settings.API_URL}/venue/{venue_id}/event/{event_id}/').json()
        self.context.update(response)
        return super(VenueEventView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.context)
        return context
