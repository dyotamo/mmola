from django.urls import path, include

from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    path('', include('mmola.urls')),
    path('admin/', admin.site.urls),
]
