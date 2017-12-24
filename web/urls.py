from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from web import views

urlpatterns = [
    url(r'^venue/(?P<venue_id>[a-zA-Z0-9]+)/event/(?P<event_id>[a-zA-Z0-9]+)/?$',
        csrf_exempt(views.VenueEventView.as_view())),
]
