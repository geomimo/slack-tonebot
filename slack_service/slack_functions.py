"""
    Functions related to Slack interactions.
    This module provides functions to extract text from Slack events and send ephemeral messages.
"""
import os
from slack_sdk import WebClient
# from slack_sdk.signature import SignatureVerifier
from dotenv import load_dotenv
from slack_sdk.errors import SlackApiError

load_dotenv()

slack_token = os.getenv("SLACK_BOT_TOKEN")
client = WebClient(token=slack_token)

def get_slack_users():
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
    
SLACK_USERS = get_slack_users()

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


def send_ephemeral_tone_message(channel_id, user_id, detected_tone):
    """
    Sends an ephemeral message to a user in a Slack channel with the detected tone.
    """
    try:
        response = client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f"""Detected tone: {detected_tone['tone'].capitalize()}\nWhy? {detected_tone['explanation']}"""
        )
        return response
    except SlackApiError as e:
        print(f"Error sending ephemeral message: {e.response['error']}")
        return None
