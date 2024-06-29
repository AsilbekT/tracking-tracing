from django.db import models
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import pytz
from timezonefinder import TimezoneFinder
from django.utils.timezone import now
from django.utils import timezone

geolocator = Nominatim(user_agent="UniqueAppIdentifierForAsilbek")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
AVERAGE_SPEED_MPH = 60


class Trailer(models.Model):
    samsara_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    def calculate_distance_to_destination(self, destination_name):
        if self.latitude is None or self.longitude is None:
            return "Location coordinates are not available."

        try:
            # Using rate limited geocode
            destination_location = geocode(destination_name)
            if not destination_location:
                return "Destination could not be geocoded."

            destination_latitude = destination_location.latitude
            destination_longitude = destination_location.longitude
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            return f"Geocoding error: {str(e)}"

        lat1, lon1, lat2, lon2 = map(radians, [
                                     self.latitude, self.longitude, destination_latitude, destination_longitude])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        R = 3958.8
        distance = R * c
        return distance

    def calculate_eta(self, destination_name):
        if self.latitude is None or self.longitude is None:
            return None, "Current location unknown"
        distance = self.calculate_distance_to_destination(destination_name)
        if isinstance(distance, str):
            return None, distance
        if distance == 0:
            return now().strftime('%Y-%m-%d %H:%M:%S'), "Arrived"
        hours_to_destination = distance / AVERAGE_SPEED_MPH
        eta_utc = timezone.now() + timedelta(hours=hours_to_destination)
        tf = TimezoneFinder()
        destination_location = geocode(destination_name)
        if not destination_location:
            return None, "Could not determine destination timezone"
        timezone_str = tf.timezone_at(
            lat=destination_location.latitude, lng=destination_location.longitude)
        if not timezone_str:
            return None, "Timezone could not be determined"
        destination_tz = pytz.timezone(timezone_str)
        eta_local = eta_utc.astimezone(destination_tz)
        return eta_local.strftime('%Y-%m-%d %H:%M:%S'), None

    def formatted_timestamp(self):
        return self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else "No timestamp available"


class Broker(models.Model):
    name = models.CharField(max_length=200)
    telegram_chat_id = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Driver(models.Model):
    name = models.CharField(max_length=200)
    license_number = models.CharField(max_length=50, unique=True)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)
    vehicle_id = models.IntegerField(primary_key=True)
    telegram_chat_id = models.CharField(
        max_length=200, unique=True, null=True, blank=True)  # New field

    def __str__(self):
        return self.name


class Load(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('delayed', 'Delayed'),
        ('finished', 'Finished'),
    ]

    load_number = models.CharField(max_length=100)
    delivery_location = models.TextField()
    delivery_time = models.DateTimeField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_driver = models.ForeignKey(
        Driver, on_delete=models.CASCADE, related_name="laods")
    assigned_trailer = models.ForeignKey(
        Trailer, on_delete=models.CASCADE, related_name="loads_trailer", null=True, blank=True)
    assigned_broker = models.ForeignKey(
        Broker, on_delete=models.CASCADE, related_name="loads_broker", null=True, blank=True)

    def is_late(self):
        if not self.assigned_trailer:
            return False, "Trailer not assigned yet."

        eta, error = self.assigned_trailer.calculate_eta(
            self.delivery_location)
        if error:
            return False, error

        try:
            eta_datetime = timezone.make_aware(datetime.strptime(
                eta, '%Y-%m-%d %H:%M:%S'), timezone.get_default_timezone())
        except ValueError as e:
            return False, f"Error parsing ETA: {str(e)}"

        if timezone.is_naive(self.delivery_time):
            delivery_time_aware = timezone.make_aware(
                self.delivery_time, timezone.get_default_timezone())
        else:
            delivery_time_aware = self.delivery_time

        if eta_datetime > delivery_time_aware:
            return True, f"Expected late delivery. ETA: {eta_datetime.strftime('%Y-%m-%d %H:%M:%S')}"
        return False, f"On time. ETA: {eta_datetime.strftime('%Y-%m-%d %H:%M:%S')}"

    def __str__(self):
        return f"Load {self.load_number}"


class TelegramMessage(models.Model):
    group_id = models.CharField(max_length=100)
    user_id = models.CharField(max_length=100)
    username = models.CharField(max_length=100, null=True, blank=True)
    text = models.TextField()
    date = models.DateTimeField()

    def __str__(self):
        return f"Message from {self.username} in group {self.group_id} at {self.date}"


class SamsaraToken(models.Model):
    token = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"{self.description} - Updated on {self.updated_at.strftime('%Y-%m-%d %H:%M:%S')}"


class TelegramBotToken(models.Model):
    token = models.CharField(max_length=255)
    bot_description = models.CharField(max_length=255, blank=True, null=True)
    # You can deactivate tokens if needed
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        status = "Active" if self.active else "Inactive"
        return f"{self.bot_description} ({status}) - Updated on {self.updated_at.strftime('%Y-%m-%d %H:%M:%S')}"
