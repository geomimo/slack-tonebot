"""
    Functions related to Slack interactions.
    This module provides functions to extract text from Slack events and send ephemeral messages.
"""
import os
from flask import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from dotenv import load_dotenv

from llm_service.llm_functions import ToneDetectionResponse

load_dotenv()

slack_token = os.getenv("SLACK_BOT_TOKEN")
client = WebClient(token=slack_token)

TONE_EMOJIS = {
            "positive": "😊",
            "negative": "😞",
            "neutral": "😐",
            "angry": "😠",
            "sad": "😢",
            "happy": "😃",
            "confused": "😕",
            "excited": "🤩"
        }

def _get_slack_users():
    """
    Fetches the list of users in the Slack workspace.
    Returns a list of user IDs and names.
    """
    try:
        response = client.users_list()
        users = response['members']
        return [(user['id'], user['name']) for user in users if not user['is_bot']]
    except SlackApiError as e:
        print(f"Error fetching users: {e.response['error']}")
        return []

SLACK_USERS = _get_slack_users()

def get_latest_message_block(channel_id, user_id):
    """
    Extracts the latest message sent from another user in the specified channel.
    Returns the message text and its ts, or None if not found.
    """
    try:
        # Fetch the latest messages from the channel
        response = client.conversations_history(channel=channel_id, limit=20)
        messages = response.get('messages', [])
        messages.sort(key=lambda x: x['ts'], reverse=True)

        # Find the latest message not sent by the bot/user
        for message in messages:
            if message.get('user') and message['user'] != user_id and 'subtype' not in message:
                return message.get('text', '')
        return None
    except SlackApiError as e:
        print(f"Error fetching messages: {e.response['error']}")
        return None

def quick_replies_button(quick_replies):
    """
    Generates a list of button elements for quick replies.
    Each reply should be a string and not exceed 75 characters.
    """
    reply_buttons = []
    for i, reply in enumerate(quick_replies):
        if isinstance(reply, str) and reply.strip() and len(reply) <= 75:
            reply_buttons.append({
                "type": "button",
                "text": {"type": "plain_text", "text": reply},
                "value": reply,
                "action_id": f"quick_reply_{i}"
            })
    return reply_buttons

def translate_button(text):
    return [{
        "type": "button",
        "text": {
            "type": "plain_text", 
            "text": "🇬🇷 Translate to Greek"
        },
        "value": text,
        "action_id": "translate_to_greek"
    }]

def send_ephemeral_tone_message(channel_id, user_id, tone_response: ToneDetectionResponse):
    """
    Sends an ephemeral message to a user in a Slack channel with the detected tone.
    """
    try:
        tone = tone_response.tone.value.lower()
        emoji = TONE_EMOJIS.get(tone, "😖")

        # Tone section
        tone_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"{emoji} *Detected Tone:* {tone.capitalize()}\n"
                        f"*Original Message:* {tone_response.original_message}\n"
                        f"*Why:* {tone_response.explanation}\n"
                        f"*Urgency:* {tone_response.urgency.value.capitalize()}\n"
                        f"*Confidence:* {tone_response.confidence}%"
                    )
                }
            }
        
        # Prepare quick reply buttons
        button_elements = []
        button_elements += quick_replies_button(tone_response.quick_replies)
        button_elements += translate_button(tone_response.original_message)

        reply_section = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Quick Replies:*" if button_elements else "_No quick replies available._"
                }
            }
        button_section ={
                "type": "actions",
                "elements": button_elements
            }         

        blocks = [
            tone_block,
            {"type": "divider"},
            reply_section,
            button_section
        ]

        response = client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=blocks,
            text="Detected tone and quick replies"
        )
        return response
    except SlackApiError as e:
        print(f"Error sending ephemeral message: {e.response['error']}")
        return None


def post_analyze_button(channel_id, user_id, message_ts):
    blocks = [
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Analyze this message"},
                    "value": message_ts,
                    "action_id": "analyze_message"
                }
            ]
        }
    ]
    client.chat_postMessage(
        channel=channel_id,
        user=user_id,
        thread_ts=message_ts,  # So it appears as a reply
        blocks=blocks,
        text="Analyze this message"
    )

    

PREFS_FILE = "user_prefs.json"

def load_user_prefs():
    if os.path.exists(PREFS_FILE):
        with open(PREFS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user_prefs(prefs):
    with open(PREFS_FILE, "w") as f:
        json.dump(prefs, f)

def is_user_opted_in(user_id):
    prefs = load_user_prefs()
    return prefs.get(user_id, False)

def set_user_opt_in(user_id, opt_in: bool):
    prefs = load_user_prefs()
    prefs[user_id] = opt_in
    save_user_prefs(prefs)

def send_simple_ephemeral_message(channel_id, user_id, text):
    """
    Sends a simple ephemeral text message to a user in a Slack channel.
    """
    try:
        response = client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=text
        )
        return response
    except SlackApiError as e:
        print(f"Error sending ephemeral message: {e.response['error']}")
        return None
      
def send_simple_message(channel_id, text):
    """
    Sends a simple text message to a Slack channel.
    """
    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=text
        )
        return response
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")
        return None
    
def send_reminder_if_no_reply(channel_id, message_ts, user_id):
    # Optionally, check again for replies here if using a DB
    client.chat_postEphemeral(
        channel=channel_id,
        user=user_id,
        text=f"<@{user_id}>, this urgent message has not been replied to in the last 10 seconds. Please follow up!"    )
