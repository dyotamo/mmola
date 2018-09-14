from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from .views.webhook import Listener

urlpatterns = [
    path('webhook/', csrf_exempt(Listener.as_view()))
]
