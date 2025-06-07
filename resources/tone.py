"""
Module for handling tone detection requests from Slack.
"""
from threading import Timer
from flask import request, Response
from flask.views import MethodView
from flask_smorest import Blueprint

from llm_service.llm_functions import detect_tone
from slack_service.slack_functions import (
    is_user_opted_in,
    post_analyze_button,
    send_ephemeral_tone_message,
    get_latest_message_block,
    send_reminder_if_no_reply,
    send_simple_ephemeral_message,
    send_simple_message,
    set_user_opt_in
)
from slack_service.payload import InteractionPayload, SlashPayload, EventPayload

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
        tone_response = detect_tone(text)
        print(tone_response)
        send_ephemeral_tone_message(payload.channel_id, payload.user_id, tone_response)
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
        
        event = payload.event
        if event['type'] == 'message' and 'subtype' not in event:
            if 'bot_id' in event:
                return '', 200
        
        user_id = event['user']
        if not is_user_opted_in(user_id):
            return '', 200
        
        # Check if button already posted for this message
        if event['ts'] in posted_buttons:
            return '', 200
        
        post_analyze_button(event['channel_id'], user_id, event['ts'])
        # Mark as posted
        posted_buttons.add(event['ts'])

        # Detect urgent messages and schedule reminder
        detected_tone = detect_tone(event['text'])
        if detected_tone.get('urgency') == 'urgent':
            timer = Timer(10, send_reminder_if_no_reply, args=(event['channel_id'], event['ts'], user_id))
            timer.start()
            pending_reminders[event['ts']] = timer

        # Step 2: Cancel reminder if a reply is posted in the thread
        if event.get('type') == 'message' and 'thread_ts' in event:
            thread_ts = event.get('thread_ts')
            if thread_ts in pending_reminders:
                timer = pending_reminders.pop(thread_ts)
                timer.cancel()

        return Response(), 200

@blp.route("/slack/interactions")
class SlackInteractions(MethodView):
    """
    Endpoint for handling Slack interactions, such as button clicks.
    This endpoint processes user interactions with the bot, such as analyzing messages or sending quick replies.
    """
    def post(self):
        payload = InteractionPayload(request)

        button_action = payload.actions[0] # Only one actions for button clicks

        if button_action['action_id'].startswith("quick_reply_"):
            send_simple_message(payload.channel['id'], button_action['value'])
        elif button_action['action_id'] == "translate_to_greek":
            pass
            # translated_text = translate_to_greek_with_tone(original_message)
            # # Send the translated message as an ephemeral message
            # send_simple_ephemeral_message(
            #     channel_id,
            #     user_id,
            #     f"🇬🇷 *Translation (tone preserved):*\n{translated_text}"
        elif button_action['action_id'] == "analyze_message":
            pass
            # # User clicked "Analyze this message"
            # message_ts = value  # This is the ts of the message to analyze

            # # Fetch the original message text
            # history = client.conversations_history(
            #     channel=channel_id, latest=message_ts, limit=1, inclusive=True
            # )
            # original_message = history["messages"][0]["text"]

            # # Run your LLM analysis
            # detected_tone = detect_tone(original_message)

            # # Send ephemeral message with quick replies to the user who clicked
            # send_ephemeral_tone_message(channel_id, user_id, detected_tone)

        return Response(), 200


posted_buttons = set()
pending_reminders = {}


@blp.route("/optin")
class OptIn(MethodView):
    @blp.response(200)
    def post(self):
        payload = SlashPayload(request)
        set_user_opt_in(payload.user_id, True)
        send_simple_ephemeral_message(payload.channel_id, payload.user_id, "You are now opted in the bot's features. Use /optout to disable them.")
        return Response(), 200

@blp.route("/optout")
class OptOut(MethodView):
    @blp.response(200)
    def post(self):
        payload = SlashPayload(request)
        set_user_opt_in(payload.user_id, False)
        send_simple_ephemeral_message(payload.channel_id, payload.user_id, "You are now opted out of the bot's features. Use /optin to enable them.")
        return Response(), 200
