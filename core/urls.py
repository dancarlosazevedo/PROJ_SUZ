from django.urls import path
from . import views

app_name = 'core'
urlpatterns = [
    path('', views.calendario_view, name='home_calendario'),
    path('api/calendar-events/', views.calendar_events_api, name='calendar_events_api'),
]
