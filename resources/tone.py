"""
Module for handling tone detection requests from Slack.
"""
from flask import request, Response
from flask.views import MethodView
from flask_smorest import Blueprint

from llm_service.llm_functions import detect_tone
from slack_service.slack_functions import (
    send_ephemeral_tone_message,
    get_latest_message_block
)
from slack_service.payload import SlashPayload, EventPayload

blp = Blueprint("Tone", "tone", description="Slash commands")

@blp.route("/detect-tone")
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
        payload = SlashPayload(request)
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
    

@blp.route("/slack/events")
class SlackEvents(MethodView):
    """
    Endpoint for handling Slack event subscriptions.
    """
    @blp.response(200)
    def post(self):
        """
        Handles incoming Slack events.
        """
        payload = EventPayload(request)

        if payload.type == "url_verification":
            return {"challenge": payload.challenge}, 200
    
    
        return Response(), 200

        
