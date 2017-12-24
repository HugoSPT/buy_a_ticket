from django.conf.urls import url, include

import api.urls
import web.urls

urlpatterns = [
    url(r'^api/', include(api.urls)),
    url(r'^', include(web.urls)),

]
