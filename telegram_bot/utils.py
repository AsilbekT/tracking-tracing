import json
import requests
import base64
from urllib.parse import urlencode
import logging

from telegram_bot.tasks import save_telegram_message
from .credentials import BOT_SETWEBHOOK_URL, SAMSARA_API_URL, SAMSARA_CLIENT_ID, SAMSARA_CLIENT_SECRET, SAMSARA_OAUTH_URL, SAMSARA_REDIRECT_URI, SAMSARA_TOKEN_URL, TELEGRAM_BOT_TOKEN, BOT_URL

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


logger = logging.getLogger(__name__)


def get_authorization_url():
    params = {
        'client_id': SAMSARA_CLIENT_ID,
        'redirect_uri': SAMSARA_REDIRECT_URI,
        'response_type': 'code',
        'state': 'random_state_string',
    }
    url = f"{SAMSARA_OAUTH_URL}?{urlencode(params)}"
    return url


def exchange_code_for_token(auth_code):
    auth_header = base64.b64encode(
        f"{SAMSARA_CLIENT_ID}:{SAMSARA_CLIENT_SECRET}".encode()).decode()
    headers = {
        'Authorization': f"Basic {auth_header}",
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': SAMSARA_REDIRECT_URI
    }
    response = requests.post(SAMSARA_TOKEN_URL, headers=headers, data=data)
    response.raise_for_status()
    return response.json()


def set_telegram_webhook():
    response = requests.get(BOT_SETWEBHOOK_URL)
    response.raise_for_status()
    return response.json()


def send_telegram_message(chat_id, text, parse_mode="HTML", reply_markup=None):
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode
    }

    if reply_markup:
        data['reply_markup'] = json.dumps(reply_markup)

    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        backoff_factor=1
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)

    try:
        logger.debug(f"Sending data to Telegram: {data}")
        response = http.post(BOT_URL + "sendMessage", data=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error sending message: {e.response.text}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error sending message: {str(e)}")
        raise


def process_telegram_message(update_json):
    """
    Process the message JSON from a Telegram update and queue the message for saving.
    Parameters:
        update_json (str): JSON string containing the Telegram message update.
    """
    try:
        update_data = json.loads(update_json)
        if 'message' in update_data:
            message = update_data['message']
            chat_id = message['chat']['id']
            user_id = message['from']['id']
            username = message['from'].get('username', 'Anonymous')
            # Handling cases where there might be no text
            text = message.get('text', '')
            message_date = message['date']

            # Queue the message saving to the Celery task
            save_telegram_message.delay(
                chat_id=chat_id,
                user_id=user_id,
                username=username,
                text=text,
                message_date=message_date
            )
            return "Message processing initiated successfully."
    except Exception as e:
        return f"Failed to process message: {str(e)}"


def approval_markup(load_id):
    return {
        "inline_keyboard": [[
            {"text": "Approve", "callback_data": f"approve_{load_id}"},
            {"text": "Reject", "callback_data": f"reject_{load_id}"}
        ]]
    }


def notify_if_late(load, telegram_chat_id):
    is_late, message = load.is_late()
    if is_late:
        send_telegram_message(telegram_chat_id, message,
                              reply_markup=approval_markup(load.load_number))


def edit_telegram_message(chat_id, message_id, text):
    data = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': text
    }
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        backoff_factor=1
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)

    try:
        logger.debug(f"Sending data to Telegram: {data}")
        response = http.post(BOT_URL + "editMessageText",
                             data=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error sending message: {e.response.text}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error sending message: {str(e)}")
        raise
