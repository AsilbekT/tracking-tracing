# services.py

from datetime import datetime
import re
from .models import Broker, Driver, TelegramMessage, Trailer, Load
import logging
import json
from django.utils import timezone

logger = logging.getLogger(__name__)


def parse_simple_load_message(message_text):
    try:
        # Parse Load Number
        load_number_match = re.search(
            r"Load Number:\s*(\d+)", message_text)
        if not load_number_match:
            raise ValueError("Load number not found.")
        load_number = load_number_match.group(1)

        # Parse Delivery Location
        delivery_location_match = re.search(
            r"Delivery Location:\s*(.+)", message_text)
        if not delivery_location_match:
            raise ValueError("Delivery location not found.")
        delivery_location = delivery_location_match.group(1)

        # Parse Delivery Time
        delivery_time_match = re.search(
            r"Delivery Time:\s*(\d{2}/\d{2}/\d{4} \d{2}:\d{2} [AP]M)", message_text)
        if not delivery_time_match:
            raise ValueError("Delivery time not found.")
        delivery_time = datetime.strptime(
            delivery_time_match.group(1), '%m/%d/%Y %I:%M %p')

        return {
            'load_number': load_number,
            'delivery_location': delivery_location,
            'delivery_time': delivery_time
        }
    except Exception as e:
        logger.error(f"Error parsing simple load message: {str(e)}")
        return None


def create_load_from_parsed_data(driver, parsed_data):
    try:
        # Create the load based on the simplified parsed data
        load = Load.objects.create(
            load_number=parsed_data['load_number'],
            delivery_location=parsed_data['delivery_location'],
            delivery_time=parsed_data['delivery_time'],
            assigned_driver=driver
        )
        # Return a success message that includes the driver's name and the newly created load details
        return f"Load {parsed_data['load_number']} successfully created and assigned to {driver.name}."
    except Exception as e:
        # Log the error and return a failure message
        logger.error(f"Error creating load: {str(e)}")
        return "An error occurred while creating the load."


def parse_load_message(command, arguments):
    try:
        if command != "/newload":
            raise ValueError("Invalid command. Expected '/newload'.")

        if len(arguments) < 3:
            raise ValueError(
                "Insufficient arguments. Expected format: /newload <load_id> <location> <time>.")

        load_number = arguments[0].strip()
        delivery_location = arguments[1].strip()
        delivery_time_str = ' '.join(arguments[2:])
        delivery_time = datetime.strptime(
            delivery_time_str, "%m/%d/%Y %I:%M %p")

        return {
            'load_number': load_number,
            'delivery_location': delivery_location,
            'delivery_time': delivery_time
        }
    except Exception as e:
        logger.error(f"Error parsing load message: {str(e)}")
        return None


def create_load_for_driver(driver, load_details):
    try:
        Load.objects.create(
            load_number=load_details['load_number'],
            delivery_location=load_details['delivery_location'],
            delivery_time=load_details['delivery_time'],
            assigned_driver=driver
        )
        return f"Load {load_details['load_number']} successfully created and assigned to {driver.name}."
    except Exception as e:
        logger.error(f"Error creating load: {str(e)}")
        return "An error occurred while creating the load."


def update_load_status(load_number, status):
    try:
        load = Load.objects.get(load_number=load_number)
        load.status = status
        load.save()
        return f"Load {load_number} status updated to {status}."
    except Load.DoesNotExist:
        return f"Load {load_number} not found."
    except Exception as e:
        logger.error(f"Error updating load status: {str(e)}")
        return "An error occurred while updating the load status."


def update_load_status_and_assign_trailer(load_number, trailer_id):
    try:
        load = Load.objects.get(load_number=load_number)
        trailer = Trailer.objects.get(name__contains=trailer_id)
        load.status = 'in_progress'
        load.assigned_trailer = trailer
        load.save()
        return f"Load {load_number} status updated to 'in_progress' and assigned to trailer {trailer_id}."
    except Load.DoesNotExist:
        return f"Load {load_number} not found."
    except Trailer.DoesNotExist:
        return f"Trailer {trailer_id} not found."
    except Exception as e:
        logger.error(
            f"Error updating load status or assigning trailer: {str(e)}")
        return "An error occurred while updating the load status or assigning the trailer."


def register_group_chat_id(name, chat_id, broker=False):
    try:
        if broker:
            obj_name = Broker
        else:
            obj_name = Driver
        obj, created = obj_name.objects.get_or_create(name=name)
        if not created and obj.telegram_chat_id:
            return f"Chat ID is already registered for {name}."
        obj.telegram_chat_id = chat_id
        obj.save()
        return f"Chat ID {chat_id} successfully registered to {'broker' if broker else 'driver'} {name}."
    except Exception as e:
        logger.error(f"Error registering chat ID: {str(e)}")
        return "An error occurred while registering the chat ID."


def get_trailer_info(trailer_id):
    try:
        trailer = Trailer.objects.get(name__contains=trailer_id)
        dest = "5260 208th St W Farmington, MN 55024"
        miles = trailer.calculate_distance_to_destination(dest)
        response_message = (
            f"Load#1669952\n"
            f"Current location: {trailer.latitude}, {trailer.longitude}\n"
            f"Miles: {int(miles)}\n"
            f"Destination: {dest}"
        )
        return response_message
    except Trailer.DoesNotExist:
        return f"Trailer with ID '{trailer_id}' not found."
    except Exception as e:
        logger.error(f"Error processing trailer information: {str(e)}")
        return "Error processing your request."


def generate_status_message(driver=None, load_id=None):
    try:
        if load_id:
            load = Load.objects.get(load_number=load_id)
            is_late, message = load.is_late()
            if is_late:
                return message, False, load
        else:
            load = driver.loads.filter(
                status="in_progress").latest('delivery_time')
        print(load, "nothing")
        trailer = load.assigned_trailer

        # Format the message with HTML
        status_message = (
            f"<b>Driver Status Update</b>\n"
            f"<b>Driver:</b> {driver.name if driver else 'N/A'}\n"
            f"<b>Load Number:</b> {load.load_number}\n"
            f"<b>Status:</b> {load.status.replace('_', ' ').title()}\n"
            f"<b>Pickup Location:</b> {load.delivery_location}\n"
            f"<b>Delivery Time:</b> {load.delivery_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        if trailer:
            status_message += (
                f"<b>Trailer:</b> {trailer.name}\n"
                f"<b>Current Location:</b> {trailer.latitude}, {trailer.longitude}\n"
                f"<b>Distance to Destination:</b> {int(trailer.calculate_distance_to_destination(load.delivery_location))} miles\n"
                f"<b>ETA:</b> {trailer.calculate_eta(load.delivery_location)[0]}\n"
            )

        status_message += "\n⚠️ <b>Please ensure all protocols are followed.</b> ⚠️"

        return status_message, True, None
    except Load.DoesNotExist:
        return "No load found with the given ID.", False, None
    except Exception as e:
        logger.error(f"Error generating status message: {str(e)}")
        return "An error occurred while generating the status message.", False, None


def process_telegram_update(update_json):
    from .tasks import save_telegram_message

    """
    Parse the incoming update from Telegram and enqueue the message for saving.
    Parameters:
        update_json (str or dict): JSON string or dictionary containing the Telegram message update.
    """
    try:
        update_data = json.loads(update_json) if isinstance(
            update_json, str) else update_json

        if 'message' in update_data:
            message = update_data['message']
            message_data = {
                'chat_id': str(message['chat']['id']),
                'user_id': str(message['from']['id']),
                'username': message['from'].get('username'),
                # Handle cases where there might be no text
                'text': message.get('text', ''),
                'date': timezone.datetime.fromtimestamp(message['date'])
            }

            # Queue the message saving to the Celery task
            save_telegram_message.delay(message_data)
            return "Message processing initiated successfully."
    except Exception as e:
        return f"Failed to process message: {str(e)}"
