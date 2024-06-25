from django.contrib import admin
from .models import Broker, Load, Trailer, Driver


@admin.register(Trailer)
class TrailerAdmin(admin.ModelAdmin):
    list_display = ('name', 'samsara_id', 'latitude', 'longitude', 'timestamp')
    search_fields = ('name', 'samsara_id')


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'license_number',
                    'phone_number', 'email', 'vehicle_id')
    search_fields = ('name', 'license_number', 'phone_number', 'email')


@admin.register(Load)
class LoadAdmin(admin.ModelAdmin):
    list_display = ('load_number', 'delivery_location',
                    'delivery_time', 'assigned_driver', 'status')
    search_fields = ('load_number', 'assigned_driver__name',
                     'delivery_location')
    list_filter = ('delivery_time', 'assigned_driver')


@admin.register(Broker)
class BrokerAdmin(admin.ModelAdmin):
    list_display = ('name', 'telegram_chat_id')
