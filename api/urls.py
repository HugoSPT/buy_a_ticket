from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from api import views

urlpatterns = [
    url(r'^1.0/venue/?$',
        csrf_exempt(views.VenueView.as_view())),
    url(r'^1.0/venues/(?P<page>[0-9]+)?$',
        csrf_exempt(views.VenuesView.as_view())),
    url(r'^1.0/venue/(?P<venue_id>[a-zA-Z0-9]+)/?$',
        csrf_exempt(views.VenueView.as_view())),
    url(r'^1.0/venue/(?P<venue_id>[a-zA-Z0-9]+)/event/?$',
        csrf_exempt(views.VenueEventView.as_view())),
    url(r'^1.0/venue/(?P<venue_id>[a-zA-Z0-9]+)/event/(?P<event_id>[a-zA-Z0-9]+)/?$',
        csrf_exempt(views.VenueEventView.as_view())),
    url(r'^1.0/venue/(?P<venue_id>[a-zA-Z0-9]+)/event/(?P<event_id>[a-zA-Z0-9]+)/reserve/?$',
        csrf_exempt(views.VenueEventReservationView.as_view())),
    url(r'^1.0/venue/(?P<venue_id>[a-zA-Z0-9]+)/event/(?P<event_id>[a-zA-Z0-9]+)/block/?$',
        csrf_exempt(views.VenueEventBlockView.as_view())),

]
