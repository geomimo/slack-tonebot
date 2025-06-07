"""
This module defines classes to represent payloads from Slack events and slash commands.
"""

import json


class SlashPayload:
    """
    Represents a Slack event payload.
    This class is used to encapsulate the data received from Slack events.
    """

    def __init__(self, request):
        form = request.form
        self.token = form.get('token')
        self.team_id = form.get('team_id')
        self.team_domain = form.get('team_domain')
        self.channel_id = form.get('channel_id')
        self.channel_name = form.get('channel_name')
        self.user_id = form.get('user_id')
        self.user_name = form.get('user_name')
        self.command = form.get('command')
        self.text = form.get('text')
        self.response_url = form.get('response_url')
        self.trigger_id = form.get('trigger_id')

class EventPayload:
    """
    Represents a Slack event payload.
    This class is used to encapsulate the data received from Slack events.
    """

    def __init__(self, request):
        json_data = request.get_json()
        self.token = json_data.get('token')
        self.team_id = json_data.get('team_id')
        self.context_team_id = json_data.get('context_team_id')
        self.context_enterprise_id = json_data.get('context_enterprise_id')
        self.api_app_id = json_data.get('api_app_id')
        self.event = json_data.get('event')
        self.type = json_data.get('type')
        self.event_id = json_data.get('event_id')
        self.event_time = json_data.get('event_time')
        self.authorizations = json_data.get('authorizations')
        self.is_ext_shared_channel = json_data.get('is_ext_shared_channel')
        self.event_context = json_data.get('event_context')
        self.challenge = json_data.get('challenge')


class InteractionPayload:
    """
    Represents a Slack interaction payload.
    This class is used to encapsulate the data received from Slack interactions.
    """

    def __init__(self, request):
        json_data = json.loads(request.form['payload'])
        self.type = json_data.get('type')
        self.token = json_data.get('token')
        self.action_ts = json_data.get('action_ts')
        self.response_url = json_data.get('response_url')
        self.user = json_data.get('user')
        self.team = json_data.get('team')
        self.container = json_data.get('container')
        self.trigger_id = json_data.get('trigger_id')
        self.actions = json_data.get('actions', [])
        self.channel = json_data.get('channel')


