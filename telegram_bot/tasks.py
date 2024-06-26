from celery import shared_task
from django.core.management import call_command
from .services import generate_status_message
from .models import Driver, TelegramMessage


@shared_task
def send_broker_updates():
    from .utils import send_telegram_message

    drivers = Driver.objects.all()
    for driver in drivers:
        assigned_loads = driver.loads.filter(status="in_progress")
        for load in assigned_loads:
            message = generate_status_message(
                driver=driver, load_id=load.load_number)
            send_telegram_message(
                load.assigned_broker.telegram_chat_id, message)


@shared_task
def update_trailer_locations():
    call_command('fetch_trailer_locations')


@shared_task
def save_telegram_message(data):
    """
    Save the message received from Telegram to the database.
    The data parameter is expected to be a dictionary.
    """
    TelegramMessage.objects.create(
        chat_id=data['chat_id'],
        user_id=data['user_id'],
        text=data['text'],
        date=data['date']
    )
