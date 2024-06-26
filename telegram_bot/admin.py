from django.contrib import admin
from .models import Broker, TelegramMessage, Load, Trailer, Driver

admin.site.site_header = "TPA Cargo Solution Updating Management"
admin.site.site_title = "TPA Cargo Admin Portal"
admin.site.index_title = "Welcome to TPA Cargo Solution Updating Management"


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


@admin.register(TelegramMessage)
class TelegramMessageAdmin(admin.ModelAdmin):
    list_display = ('group_id', 'user_id', 'username', 'text', 'date')
    list_filter = ('group_id', 'username', 'date')
    search_fields = ('group_id', 'username', 'text')
    readonly_fields = ('group_id', 'user_id', 'username', 'text', 'date')
    ordering = ('-date',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
