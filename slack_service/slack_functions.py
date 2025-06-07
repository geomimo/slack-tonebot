"""
    Functions related to Slack interactions.
    This module provides functions to extract text from Slack events and send ephemeral messages.
"""
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from dotenv import load_dotenv

load_dotenv()

slack_token = os.getenv("SLACK_BOT_TOKEN")
slack_signing_secret = os.getenv("MY_SLACK_SIGNING_SECRET")
client = WebClient(token=slack_token)

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

class SlackPayload:
    """
    Represents a Slack event payload.
    This class is used to encapsulate the data received from Slack events.
    """

    def __init__(self, request_form):
        self.token = request_form['token']
        self.team_id = request_form.get('team_id')
        self.team_domain = request_form.get('team_domain')
        self.channel_id = request_form.get('channel_id')
        self.channel_name = request_form.get('channel_name')
        self.user_id = request_form.get('user_id')
        self.user_name = request_form.get('user_name')
        self.command = request_form.get('command')
        self.text = request_form.get('text')
        self.response_url = request_form.get('response_url')
        self.trigger_id = request_form.get('trigger_id')

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


tone_emojis = {
    "positive": "😊",
    "negative": "😞",
    "neutral": "😐",
    "angry": "😠",
    "sad": "😢",
    "happy": "😄",
    "confused": "😕",
    "excited": "🤩"
}


def send_ephemeral_tone_message(channel_id, user_id, detected_tone):
    try:
        tone = detected_tone.get('tone', 'N/A')
        emoji = tone_emojis.get(tone.lower(), "")  # get emoji or empty if not found
        # Compose the message blocks
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Original message:* {detected_tone.get('original_message', 'N/A')}\n"
                        f"*Detected tone:* {detected_tone.get('tone', 'N/A').capitalize()} {emoji}\n"
                        f"*Why:* {detected_tone.get('explanation', 'No explanation available.')}\n"
                        f"*Urgency:* {detected_tone.get('urgency', 'N/A')}\n"
                        f"*Confidence:* {detected_tone.get('confidence', 'N/A')}%"
                    )
                }
            }
            # ,{
            #     "type": "actions",
            #     "elements": [
            #         {
            #             "type": "button",
            #             "text": {"type": "plain_text", "text": reply},
            #             "value": reply,
            #             "action_id": f"quick_reply_{i}"
            #         }
            #         for i, reply in enumerate(detected_tone.get("quick_replies", []))
            #     ]
            # }
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
    