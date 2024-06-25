import os
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
# from your_app_name import consumers

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tracking.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
})
