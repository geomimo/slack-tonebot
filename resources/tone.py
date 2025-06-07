"""
Module for handling tone detection requests from Slack.
"""
from flask import request, Response, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from slack_sdk import WebClient
import json
import os


from llm_service.llm_functions import detect_tone
from slack_service.slack_functions import (
    SlackPayload,
    send_ephemeral_tone_message,
    get_latest_message_block
)

blp = Blueprint("Tone", "tone", description="Slash commands")

@blp.route("/detect-tone-louk")
class ToneDetection(MethodView):
    """
    Endpoint for detecting the tone of a message sent via Slack.
    This endpoint processes a Slack event, extracts the message text, and detects its tone.
    """
    @blp.response(200)
    def post(self):
        """
        Detects the tone of a message sent via Slack.
        """
        payload = SlackPayload(request.form)
        text = payload.text
        if text is None or text == "":
            text = get_latest_message_block(payload.channel_id, payload.user_id)
        print("Text to analyze:", text)
        tone_dictionary = detect_tone(text)
        print(tone_dictionary)
        send_ephemeral_tone_message(payload.channel_id, payload.user_id, tone_dictionary)
        return Response(), 200

    @blp.response(200)
    def get(self):
        """
        Test endpoint to verify the service is running.
        """
        return "hello there"

# slack_interactions = Blueprint('slack_interactions', __name__)

# @slack_interactions.route("/slack/interactions", methods=["POST"])
# def handle_interaction():
#     payload = json.loads(request.form["payload"])
#     user_id = payload["user"]["id"]
#     channel_id = payload["channel"]["id"]
#     actions = payload["actions"]
#     action = actions[0]
#     quick_reply = action["value"]  # The button value you set

#     # Send the quick reply as a message in the channel
#     client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
#     client.chat_postMessage(channel=channel_id, text=quick_reply)

#     # Optionally, update the original ephemeral message or acknowledge the action
#     return jsonify({"text": f"Sent: {quick_reply}"})


# slack_events = Blueprint('slack_events', __name__)

# @slack_events.route('/events', methods=['POST'])
# def handle_events():
#     data = request.get_json()
#     if data.get('type') == 'url_verification':
#         return data.get('challenge')
