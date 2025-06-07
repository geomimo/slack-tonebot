"""
Module for handling tone detection requests from Slack.
"""
from flask import request, Response, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from slack_sdk import WebClient
from threading import Timer
import json
import os
import re


from llm_service.llm_functions import detect_tone, translate_to_greek_with_tone, summarize_conversation
from slack_service.slack_functions import (
    SlackPayload,
    send_ephemeral_tone_message,
    get_latest_message_block,
    post_analyze_button,
    is_user_opted_in,
    set_user_opt_in,
    send_simple_ephemeral_message,
    send_reminder_if_no_reply,
    conversations_replies
)

slack_token = os.getenv("SLACK_BOT_TOKEN")
slack_signing_secret = os.getenv("MY_SLACK_SIGNING_SECRET") 
client = WebClient(token=slack_token)

blp = Blueprint("Tone", "tone", description="Slash commands")

@blp.route("/detect-tone-lagk")
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
slack_events = Blueprint('slack_events', __name__)

posted_buttons = set()
pending_reminders = {}

@slack_events.route('/events', methods=['POST'])
def handle_events():
    data = request.get_json()
    if data.get('type') == 'url_verification':
        return data.get('challenge')

    event = data.get('event', {})

    # Step 1: Handle new user messages
    if event.get('type') == 'message' and 'subtype' not in event:
        if 'bot_id' in event:
            return '', 200
        user_id = event.get('user')
        if not is_user_opted_in(user_id):
            return '', 200      
        channel_id = event.get('channel')
        message_ts = event.get('ts')
        message_text = event.get('text')

        # Check if button already posted for this message
        if message_ts in posted_buttons:
            return '', 200

        # Post the analyze button
        post_analyze_button(channel_id, user_id, message_ts)

        # Mark as posted
        posted_buttons.add(message_ts)

        # Detect urgent messages and schedule reminder
        detected_tone = detect_tone(message_text)
        if detected_tone.get('urgency') == 'urgent':
            timer = Timer(10, send_reminder_if_no_reply, args=(channel_id, message_ts, user_id))
            timer.start()
            pending_reminders[message_ts] = timer

    # Step 2: Cancel reminder if a reply is posted in the thread
    if event.get('type') == 'message' and 'thread_ts' in event:
        thread_ts = event.get('thread_ts')
        if thread_ts in pending_reminders:
            timer = pending_reminders.pop(thread_ts)
            timer.cancel()

    return '', 200

slack_interactions = Blueprint('slack_interactions', __name__)

@slack_interactions.route("/slack/interactions", methods=["POST"])
def handle_interaction():
    payload = json.loads(request.form["payload"])
    user_id = payload["user"]["id"]
    if not is_user_opted_in(user_id):
        return jsonify({"text": "You are currently opted out of the bot's features. Use /opt-in to enable them."})
    channel_id = payload["channel"]["id"]
    action = payload["actions"][0]  # Assuming single action for simplicity
    action_id = action.get("action_id")
    value = action.get("value")

    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

    if action_id == "analyze_message":
        # User clicked "Analyze this message"
        message_ts = value  # This is the ts of the message to analyze

        # Fetch the original message text
        history = client.conversations_history(
            channel=channel_id, latest=message_ts, limit=1, inclusive=True
        )
        original_message = history["messages"][0]["text"]

        # Run your LLM analysis
        detected_tone = detect_tone(original_message)

        # Send ephemeral message with quick replies to the user who clicked
        send_ephemeral_tone_message(channel_id, user_id, detected_tone)

        return jsonify({"text": "Analyzing message..."})

    elif action_id and action_id.startswith("quick_reply_"):
        # User clicked a quick reply button
        quick_reply = value  # The button value you set

        # Send the quick reply as a message in the channel
        client.chat_postMessage(channel=channel_id, text=quick_reply)

        return jsonify({"text": f"Sent: {quick_reply}"})
    elif action_id == "translate_to_greek":
        original_message = value  # The button's value is the original message text
        # Call your translation function
        translated_text = translate_to_greek_with_tone(original_message)
        # Send the translated message as an ephemeral message
        send_simple_ephemeral_message(
            channel_id,
            user_id,
            f"🇬🇷 *Translation (tone preserved):*\n{translated_text}"
        )
        return jsonify({"text": "Translated to Greek!"})

    else:
        # Unknown action
        return jsonify({"text": "Unknown action."}), 400
    
@blp.route("/optin")
class OptIn(MethodView):
    @blp.response(200)
    def post(self):
        payload = SlackPayload(request.form)
        set_user_opt_in(payload.user_id, True)
        send_simple_ephemeral_message(payload.channel_id, payload.user_id, "You are now opted in the bot's features. Use /optout to disable them.")
        return Response(), 200

@blp.route("/optout")
class OptOut(MethodView):
    @blp.response(200)
    def post(self):
        payload = SlackPayload(request.form)
        set_user_opt_in(payload.user_id, False)
        send_simple_ephemeral_message(payload.channel_id, payload.user_id, "You are now opted out of the bot's features. Use /optin to enable them.")
        return Response(), 200
    
def extract_channel_and_ts_from_link(link):
    m = re.search(r'/archives/([A-Z0-9]+)/p(\d{16})', link)
    if m:
        channel_id = m.group(1)
        ts = m.group(2)
        ts = ts[:-6] + '.' + ts[-6:]
        return channel_id, ts
    return None, None

@blp.route("/summarizethread")
class SummarizeThread(MethodView):
    @blp.response(200)
    def post(self):
        payload = SlackPayload(request.form)
        user_id = payload.user_id
        text = payload.text.strip()
        # Try to extract channel and thread_ts from the pasted link
        channel_id, thread_ts = extract_channel_and_ts_from_link(text)
        if not (channel_id and thread_ts):
            send_simple_ephemeral_message(
                payload.channel_id,
                user_id,
                "Please provide a valid thread link with /summarizethread."
            )
            return "", 200

        # Fetch all messages in the thread
        response = client.conversations_replies(channel=channel_id, ts=thread_ts)
        messages = response['messages']
        user_messages = [m for m in messages if 'user' in m and 'text' in m]

        summary = summarize_conversation(user_messages)
        send_simple_ephemeral_message(
            channel_id,
            user_id,
            f"*Summary of the thread:*\n{summary}"
        )
        return "", 200