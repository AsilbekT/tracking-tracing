from django.db import models
from math import radians, sin, cos, sqrt, atan2
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from datetime import datetime
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

geolocator = Nominatim(user_agent="UniqueAppIdentifierForAsilbek")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)


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

    def formatted_timestamp(self):
        return self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else "No timestamp available"


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
        ('finished', 'Finished'),
    ]

    load_number = models.CharField(max_length=100)
    delivery_location = models.TextField()
    delivery_time = models.DateTimeField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_driver = models.ForeignKey(
        Driver, on_delete=models.CASCADE, related_name="loads")
    assigned_trailer = models.ForeignKey(
        Trailer, on_delete=models.CASCADE, related_name="loads", null=True, blank=True)

    def __str__(self):
        return f"Load {self.load_number}"


class Broker(models.Model):
    name = models.CharField(max_length=200)
    telegram_chat_id = models.CharField(max_length=200)

    def __str__(self):
        return self.name
