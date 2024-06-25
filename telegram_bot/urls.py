# telegram_bot/urls.py

from django.urls import path
from .views import Hook, SetWebHook

urlpatterns = [
    path('webhook/', Hook.as_view(), name='webhook'),
    path('set_webhook/', SetWebHook.as_view(), name='set_webhook'),

]
