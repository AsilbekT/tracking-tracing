from datetime import timedelta

CELERY_BEAT_SCHEDULE = {
    'send-broker-updates-every-10-seconds': {
        'task': 'telegram_bot.tasks.send_broker_updates',
        'schedule': timedelta(seconds=10),
    },
}
