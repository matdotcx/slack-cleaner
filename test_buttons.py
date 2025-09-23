#!/usr/bin/env python3
import os
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")

app = App(token=SLACK_BOT_TOKEN)

@app.command("/test-button")
def test_button_command(ack, body, client):
    ack()

    user_id = body["user_id"]

    client.chat_postMessage(
        channel=user_id,
        text="Button Test",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Click the button below to test if buttons work!"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Click Me!"
                        },
                        "action_id": "test_button_click",
                        "value": "button_clicked"
                    }
                ]
            }
        ]
    )

@app.action("test_button_click")
def handle_button_click(ack, body, client):
    ack()

    logger.info("BUTTON CLICKED! Body: %s", body)

    user_id = body["user"]["id"]

    client.chat_postMessage(
        channel=user_id,
        text=f"✅ SUCCESS! Button click was received! User: <@{user_id}>"
    )

if __name__ == "__main__":
    logger.info("Starting button test app...")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()