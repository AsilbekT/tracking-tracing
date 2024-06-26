from django.http import JsonResponse
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json
from .services import create_load_for_driver, create_load_from_parsed_data, generate_status_message, get_trailer_info, parse_simple_load_message, process_telegram_update, register_group_chat_id, update_load_status, update_load_status_and_assign_trailer
from .utils import approval_markup, edit_telegram_message, send_telegram_message, set_telegram_webhook
from .models import Load, Trailer, Driver
import logging

logger = logging.getLogger(__name__)


class Hook(APIView):
    def post(self, request, *args, **kwargs):
        try:
            update = json.loads(request.body)
            print(update)

            # Handling different types of updates
            if "callback_query" in update.keys():
                return self.handle_callback(update['callback_query'])
            elif 'message' in update:
                return self.handle_message(update['message'])
            elif 'my_chat_member' in update:
                return self.handle_chat_member_update(update['my_chat_member'])
            else:
                logger.error("Received unknown update type")
                return Response({'error': 'Received unknown update type'}, status=status.HTTP_400_BAD_REQUEST)

        except json.JSONDecodeError:
            return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unhandled exception: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def handle_callback(self, callback_query):
        callback_data = callback_query['data']
        message_id = callback_query['message']['message_id']
        chat_id = callback_query['message']['chat']['id']

        if "approve_" in callback_data:
            load_id = callback_data.split('_')[1]
            print(message_id, load_id)
            try:
                load_instance = Load.objects.get(load_number=load_id)
                broker_chat_id = load_instance.assigned_broker.telegram_chat_id
                print(broker_chat_id)
                response_message = generate_status_message(
                    load_id=load_instance.load_number)
                send_telegram_message(chat_id=broker_chat_id,
                                      text=response_message)
                edit_telegram_message(
                    chat_id, message_id, "Update approved. Notifying broker.")
            except Load.DoesNotExist:
                edit_telegram_message(
                    chat_id, message_id, "Failed to find the load. It might have been removed.")
                return Response({'error': 'Load not found'}, status=status.HTTP_404_NOT_FOUND)

        elif "reject_" in callback_data:
            load_id = callback_data.split('_')[1]
            try:
                load_instance = Load.objects.get(load_number=load_id)
                edit_telegram_message(
                    chat_id, message_id, "Update rejected. No action taken.")
            except Load.DoesNotExist:
                edit_telegram_message(
                    chat_id, message_id, "Failed to find the load. It might have been removed.")
                return Response({'error': 'Load not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'message': "Callback processed"}, status=status.HTTP_200_OK)

    def handle_message(self, message):
        chat_id = message['chat']['id']
        chat_name = message['chat'].get('title', 'Unknown Group')
        message_text = message.get('text', '')

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

        elif command == "/register_driver":
            response_message = register_group_chat_id(chat_name, chat_id)
            return self.respond_with_message(chat_id, response_message)

        elif command == "/register_broker":
            response_message = register_group_chat_id(
                chat_name, chat_id, broker=True)
            return self.respond_with_message(chat_id, response_message)

        elif command == "/status":
            if arguments:
                load_id = arguments[0]
                response_message, is_ok, load_obj = generate_status_message(
                    load_id=load_id)
                if not is_ok:
                    self.respond_with_message(
                        chat_id, "There is a problem with server, please try again later")
                    return self.respond_with_message(-4228802948, response_message, reply_markup=approval_markup(load_obj.load_number))
            else:
                driver = Driver.objects.get(telegram_chat_id=chat_id)
                response_message, is_ok, load_obj = generate_status_message(
                    driver=driver)
            return self.respond_with_message(chat_id, response_message)

        elif command == "/in_progress":
            if len(arguments) >= 2:
                load_number, trailer_id = arguments[0], arguments[1]
                response_message = update_load_status_and_assign_trailer(
                    load_number, trailer_id)
            else:
                response_message = "Invalid format. Use: /in_progress <load_number> <trailer_id>"
            return self.respond_with_message(chat_id, response_message)

        elif command == "/finish":
            if arguments:
                load_number = arguments[0]
                response_message = update_load_status(
                    load_number, 'finished')
                return self.respond_with_message(chat_id, response_message)
            else:
                return Response({'error': 'Load number is required for /finish command'}, status=status.HTTP_400_BAD_REQUEST)

        elif "trailer#" in message_text:
            trailer_id = message_text.split("trailer#")[1].strip()
            response_message = get_trailer_info(trailer_id)
            return self.respond_with_message(chat_id, response_message)

        else:
            return Response({'error': 'Unknown command'}, status=status.HTTP_200_OK)

    def handle_chat_member_update(self, chat_member_update):
        # Log or handle chat member updates
        logger.info(f"Chat member update received: {chat_member_update}")
        # Return a simple acknowledgment or perform any needed actions
        return Response({'message': "Chat member update processed"}, status=status.HTTP_200_OK)

    def respond_with_message(self, chat_id, message, reply_markup=None):
        if reply_markup:
            send_telegram_message(
                chat_id, message, parse_mode="HTML", reply_markup=reply_markup)
        else:
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
