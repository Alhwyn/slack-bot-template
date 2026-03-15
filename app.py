from slack_bolt import App
from slack_sdk.errors import SlackApiError
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request, jsonify
import os
import json
import logging
import requests
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())

SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_BOT_USER_ID = os.getenv('SLACK_BOT_USER_ID')
NANOBOT_URL = os.getenv('NANOBOT_URL')

logger = logging.getLogger(__name__)

flask_app = Flask(__name__)
app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)


handler = SlackRequestHandler(app)


# listen fur user mentoining the slack app
@app.event("app_mention")
def event_test(body, say, logger):
    logger.info(body)
    say("What's up?")

@app.event("message")
def handle_message_events(body, say, logger):
    logger.info(body)
    event = body.get("event", {})
    message = event.get("text", "")
    user_id = event.get("user")
    channel = event.get("channel")

    # Ignore own messages and bot messages
    if not user_id or user_id == SLACK_BOT_USER_ID or event.get("bot_id"):
        return

    try:
        response = requests.post(
            f"{NANOBOT_URL}/webhook",
            json={
                "content": message,
                "channel": "slack",
                "chat_id": channel,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        reply = data.get("response") or data.get("message", "")
        if reply:
            say(text=reply, channel=channel)
    except Exception as e:
        logger.error(f"Error forwarding message to nanobot: {e}")
        say(text="Beklager, jeg kunne ikke behandle meldingen din akkurat nå.", channel=channel)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)



@app.command("/nanobot")
def nanobot_command(ack, say, body, command, logger, client):
    ack()
    text = command.get("text", "").strip()
    user_id = body.get("user_id")
    channel_id = body.get("channel_id")

    if not text:
        say(text="Bruk: `/nanobot <melding>`", channel=channel_id)
        return

    try:
        response = requests.post(
            f"{NANOBOT_URL}/webhook",
            json={
                "content": text,
                "channel": "slack",
                "chat_id": channel_id,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        reply = data.get("response") or data.get("message", "")
        if reply:
            say(text=reply, channel=channel_id)
        else:
            say(text="Nanobot svarte uten innhold.", channel=channel_id)
    except Exception as e:
        logger.error(f"Error in /nanobot command: {e}")
        say(text="Beklager, nanobot er ikke tilgjengelig akkurat nå.", channel=channel_id)


@app.command("/command_example")
def pricing_command(ack, say, body,  command, logger, client):
    ack()
    trigger_id = body['trigger_id']
    try:
        with open('command_example.json') as file:      
            json_data = json.load(file)
            say(json_data)
    except Exception as e:
        logger.error(f"Error Handling in /command_example {e}")


@app.command("/modal_example")
def pricing_command(ack, say, body,  command, logger, client):
    ack()
    trigger_id = body['trigger_id']
    try:
        with open('modal_example.json') as file:
            json_data = json.load(file)
            client.views_open(trigger_id=trigger_id, view=json_data)
    except Exception as e:
                logger.error(f"Error Handling in /modal_example {e}")

@app.view("modal_example")
def handle_pricing_submission(ack, body, logger):
    ack()
    try:
        print('pricing modals works')
    except Exception as e:
        logger.error(f"Error Handling modal_example{e}")

@app.command("/button_example")
def pricing_command(ack, say, body,  command, logger, client):
    ack()
    trigger_id = body['trigger_id']
    try:
        with open('button_example.json') as file:      
            json_data = json.load(file)
            say(json_data)
    except Exception as e:
        logger.error(f"Error Handling /button_example {e}")

@app.action("actionId-0")
def pricing_command(ack, say, body, logger, client):
    ack()
    trigger_id = body['trigger_id']
    try:
        with open('example.json') as file:      
            json_data = json.load(file)
            say(trigger_id=trigger_id, blocks=json_data['blocks'])

    except Exception as e:
        logger.error(f"Error Handling hactionId-0 {e}")


if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=5000)
