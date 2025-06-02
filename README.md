# Slack ToneBot

Slack ToneBot is a bot for Slack that analyzes the tone of messages in your workspace and provides feedback or suggestions to improve communication.

## Features

- Analyzes message tone (positive, negative, neutral)
- Provides real-time feedback in channels or DMs
- Customizable responses and tone thresholds
- Easy integration with your Slack workspace

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/slack-tonebot.git
    cd slack-tonebot
    ```
2. Create a python environment:
    ```bash
    python -m venv venv 
    ```
3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Set up your environment variables:
    - Create a file named `.env`
    - Set your environment variables
5. Start the bot:
    ```bash
    run.bat
    ```

## Project Structure
The project is structured in such a way to decouple the logic of the application and allow faster developing from multiple devs.

- `/llm_service/`: Handles interactions with the LLM API
    - `llm_functions`: Functions for communicating with the LLM API
- `/slack_service/`: Handles interactions with the Slack API
    - `slack_function`: Functions for communicating with the Slack API
- `/resources/`: Application endpoints
    - `tone`: Defines endpoints for slash commands and coordinates the logic
- `app.py`: Initializes the Flask application
- `run.bat`: Runs the Flask application and ngrok
