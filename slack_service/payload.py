"""
This module defines classes to represent payloads from Slack events and slash commands.
"""

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
        self.challenge = json_data.get('challenge')
        self.type = json_data.get('type')