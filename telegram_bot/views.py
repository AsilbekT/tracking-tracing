from django.http import JsonResponse
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json
from .services import create_load_for_driver, create_load_from_parsed_data, generate_status_message, get_trailer_info, parse_simple_load_message, register_group_chat_id, update_load_status, update_load_status_and_assign_trailer
from .utils import send_telegram_message, set_telegram_webhook
from .models import Trailer, Driver
import logging

logger = logging.getLogger(__name__)


class Hook(APIView):
    def post(self, request, *args, **kwargs):
        update = json.loads(request.body)
        if 'message' not in update or 'chat' not in update['message']:
            logger.error("Invalid message format or structure")
            return Response({'error': 'Invalid message format'}, status=status.HTTP_400_BAD_REQUEST)

        chat_id = update['message']['chat']['id']
        chat_name = update['message']['chat'].get('title', 'Unknown Group')
        message_text = update['message'].get('text', '')

        command_parts = message_text.split()
        if not command_parts:
            return self.respond_with_message(chat_id, "No command found in the message.")

        command = command_parts[0]
        arguments = command_parts[1:]

        if command == "/newload":
            parsed_data = parse_simple_load_message(message_text)
            if parsed_data:
                try:
                    driver = Driver.objects.get(telegram_chat_id=chat_id)
                    response_message = create_load_from_parsed_data(
                        driver, parsed_data)
                except Driver.DoesNotExist:
                    response_message = "Driver not registered with this chat ID."
                return self.respond_with_message(chat_id, response_message)
            else:
                return self.respond_with_message(chat_id, "Failed to parse load details.")

        if command == "/register_driver":
            response_message = register_group_chat_id(chat_name, chat_id)
            return self.respond_with_message(chat_id, response_message)

        if command == "/register_broker":
            response_message = register_group_chat_id(
                chat_name, chat_id, broker=True)
            return self.respond_with_message(chat_id, response_message)

        if command == "/status":
            try:
                driver = Driver.objects.get(telegram_chat_id=chat_id)
                response_message = generate_status_message(driver)
            except Driver.DoesNotExist:
                response_message = "Driver not registered with this chat ID."
            return self.respond_with_message(chat_id, response_message)

        elif command == "/in_progress":
            try:
                load_number, trailer_id = arguments[0], arguments[1]
                response_message = update_load_status_and_assign_trailer(
                    load_number, trailer_id)
            except IndexError:
                response_message = "Invalid format. Use: /in_progress <load_number> <trailer_id>"
            return self.respond_with_message(chat_id, response_message)

        elif command == "/finish":
            load_number = arguments[0]
            response_message = update_load_status(load_number, 'finished')
            return self.respond_with_message(chat_id, response_message)

        if "trailer#" in message_text:
            trailer_id = message_text.split("trailer#")[1].strip()
            response_message = get_trailer_info(trailer_id)
            return self.respond_with_message(chat_id, response_message)

        return self.respond_with_message(chat_id, "Invalid message format.")

    def respond_with_message(self, chat_id, message):
        send_telegram_message(chat_id, message, parse_mode="HTML")
        return Response({'message': "Processed"}, status=status.HTTP_200_OK)


class SetWebHook(APIView):
    def get(self, request, *args, **kwargs):
        try:
            response = set_telegram_webhook()
            return Response({'message': response}, status=status.HTTP_200_OK)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to set webhook: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
