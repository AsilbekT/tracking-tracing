from celery import shared_task

from telegram_bot.services import generate_status_message
from .utils import send_telegram_message
from .models import Driver

from django.core.management import call_command


@shared_task
def send_broker_updates():
    broker_group_chat_id = '-4228802948'
    drivers = Driver.objects.all()
    for driver in drivers:
        message = generate_status_message(driver)
    send_telegram_message(broker_group_chat_id, message)


@shared_task
def update_trailer_locations():
    call_command('fetch_trailer_locations')
