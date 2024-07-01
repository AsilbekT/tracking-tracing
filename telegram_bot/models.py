from django.db import models
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
import requests
from django.utils.timezone import now
from django.utils import timezone
import pytz
from timezonefinder import TimezoneFinder

from telegram_bot.credentials import MAPBOX_API_KEY

AVERAGE_SPEED_MPH = 60


class Trailer(models.Model):
    samsara_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    def geocode_destination(self, destination_name):
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{destination_name}.json"
        params = {
            'access_token': MAPBOX_API_KEY,
            'limit': 1
        }
        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code == 200 and data['features']:
            destination = data['features'][0]['geometry']['coordinates']
            return destination[1], destination[0]  # latitude, longitude
        else:
            return None, f"Geocoding error: {data.get('message', 'Unable to fetch geocode')}"

    def calculate_distance_to_destination(self, destination_name):
        if self.latitude is None or self.longitude is None:
            return "Location coordinates are not available."

        destination_latitude, destination_longitude = self.geocode_destination(
            destination_name)
        if destination_latitude is None:
            return destination_longitude  # This is the error message

        url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{self.longitude},{self.latitude};{destination_longitude},{destination_latitude}"
        params = {
            'access_token': MAPBOX_API_KEY,
            'geometries': 'geojson'
        }
        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code == 200 and data['routes']:
            distance_meters = data['routes'][0]['distance']
            distance_miles = distance_meters / 1609.34  # Convert meters to miles
            return distance_miles
        else:
            return f"Error: {data.get('message', 'Unable to fetch distance')}"

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
        destination_latitude, destination_longitude = self.geocode_destination(
            destination_name)
        if destination_latitude is None:
            return None, destination_longitude  # This is the error message
        timezone_str = tf.timezone_at(
            lat=destination_latitude, lng=destination_longitude)
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
        Driver, on_delete=models.CASCADE, related_name="loads")
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
