import os
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

import config
import database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config.validate_config()
database.init_db()

app = App(
    token=config.SLACK_BOT_TOKEN,
    signing_secret=config.SLACK_SIGNING_SECRET
)

user_client = WebClient(token=config.SLACK_USER_TOKEN)

@app.message_shortcut("delete_my_message")
def handle_message_shortcut(ack, body, client, logger):
    ack()

    user_id = body["user"]["id"]
    message = body["message"]
    channel_id = body["channel"]["id"]
    message_ts = message["ts"]
    message_user_id = message.get("user", "")
    message_text = message.get("text", "")

    logger.info(f"Deletion request: user={user_id}, channel={channel_id}, msg_user={message_user_id}")

    if user_id != message_user_id:
        try:
            client.chat_postMessage(
                channel=user_id,
                text=f"❌ You can only request deletion of your own messages."
            )
        except:
            pass
        return

    try:
        user_info = client.users_info(user=user_id)
        requester_name = user_info["user"]["real_name"]

        try:
            channel_info = client.conversations_info(channel=channel_id)
            channel_name = channel_info["channel"]["name"]
        except:
            channel_name = "Unknown"

        try:
            message_link = client.chat_getPermalink(
                channel=channel_id,
                message_ts=message_ts
            )["permalink"]
        except:
            message_link = f"Channel: {channel_id}, TS: {message_ts}"

        preview_text = message_text[:200] + "..." if len(message_text) > 200 else message_text

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🗑️ New Deletion Request"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Requester:*\n<@{user_id}>"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Channel:*\n<#{channel_id}>"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Message:*\n```{preview_text}```"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"<{message_link}|View original message>"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "actions",
                "block_id": "deletion_actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ Approve Deletion"
                        },
                        "style": "primary",
                        "action_id": "approve_deletion",
                        "value": f"{channel_id}|{message_ts}|{user_id}"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "❌ Deny Request"
                        },
                        "style": "danger",
                        "action_id": "deny_deletion",
                        "value": f"{channel_id}|{message_ts}|{user_id}"
                    }
                ]
            }
        ]

        admin_message = client.chat_postMessage(
            channel=config.ADMIN_REVIEW_CHANNEL,
            blocks=blocks,
            text=f"Deletion request from {requester_name}"
        )

        request_id = database.create_deletion_request(
            message_ts=message_ts,
            channel_id=channel_id,
            channel_name=channel_name,
            message_author_id=user_id,
            message_author_name=requester_name,
            message_text=message_text,
            requester_id=user_id,
            requester_name=requester_name,
            admin_message_ts=admin_message["ts"]
        )

        client.chat_postMessage(
            channel=user_id,
            text=f"✅ Your deletion request has been submitted to the admins for review.\n\nMessage from <#{channel_id}>:\n```{preview_text}```"
        )

        logger.info(f"Deletion request created: ID={request_id}, User={user_id}, Channel={channel_id}")

    except Exception as e:
        logger.error(f"Error handling deletion request: {e}")
        try:
            client.chat_postMessage(
                channel=user_id,
                text=f"❌ Error submitting deletion request: {str(e)}"
            )
        except:
            pass

@app.action("approve_deletion")
def handle_approve_deletion(ack, body, client, logger):
    ack()

    admin_id = body["user"]["id"]
    admin_name = body["user"]["name"]

    if not config.is_admin(admin_id):
        try:
            client.chat_postMessage(
                channel=admin_id,
                text="❌ You are not authorized to approve deletion requests."
            )
        except:
            pass
        return

    try:
        admin_message_ts = body["message"]["ts"]

        request = database.get_deletion_request_by_admin_message(admin_message_ts)

        if not request:
            raise ValueError("Deletion request not found in database")

        value_parts = body["actions"][0]["value"].split("|")
        channel_id = value_parts[0]
        message_ts = value_parts[1]
        requester_id = value_parts[2]

        try:
            deletion_result = user_client.chat_delete(
                channel=channel_id,
                ts=message_ts
            )

            if not deletion_result.get("ok"):
                raise Exception(f"Deletion failed: {deletion_result.get('error', 'Unknown error')}")

            database.update_deletion_request(
                request_id=request["id"],
                status="approved",
                admin_id=admin_id,
                admin_name=admin_name
            )

            updated_blocks = body["message"]["blocks"][:-1]
            updated_blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"✅ *Approved by <@{admin_id}> at <!date^{int(body['actions'][0]['action_ts'])}^{{date_short_pretty}} {{time}}|{body['actions'][0]['action_ts']}>*"
                    }
                ]
            })

            client.chat_update(
                channel=body["channel"]["id"],
                ts=admin_message_ts,
                blocks=updated_blocks,
                text=f"Deletion request approved by {admin_name}"
            )

            client.chat_postMessage(
                channel=requester_id,
                text=f"✅ Your message deletion request has been approved by <@{admin_id}> and the message has been deleted."
            )

            if config.AUDIT_LOG_CHANNEL:
                client.chat_postMessage(
                    channel=config.AUDIT_LOG_CHANNEL,
                    text=f"🗑️ Message deleted by <@{admin_id}>\n• Author: <@{request['message_author_id']}>\n• Channel: <#{channel_id}>\n• Timestamp: {message_ts}"
                )

            logger.info(f"Deletion approved: ID={request['id']}, Admin={admin_id}")

        except Exception as e:
            error_str = str(e)
            if "message_not_found" in error_str:
                error_msg = "The message may have already been deleted."
            elif "channel_not_found" in error_str or "not_in_channel" in error_str:
                error_msg = "⚠️ Bot must be invited to the channel to delete messages. Please invite the bot to the channel and try again."
            else:
                error_msg = f"Error: {error_str}"

            database.update_deletion_request(
                request_id=request["id"],
                status="error",
                admin_id=admin_id,
                admin_name=admin_name,
                notes=error_msg
            )

            updated_blocks = body["message"]["blocks"][:-1]
            updated_blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"❌ *Error by <@{admin_id}>:* {error_msg}"
                    }
                ]
            })

            client.chat_update(
                channel=body["channel"]["id"],
                ts=admin_message_ts,
                blocks=updated_blocks,
                text=f"Deletion failed: {error_msg}"
            )

            client.chat_postMessage(
                channel=requester_id,
                text=f"❌ Your deletion request could not be completed.\n\nReason: {error_msg}\n\nIf the bot needs to be invited to the channel, please ask an admin to invite it: `/invite @{client.auth_test()['user']}`"
            )
            return

    except Exception as e:
        logger.error(f"Error approving deletion: {e}")
        try:
            client.chat_postMessage(
                channel=admin_id,
                text=f"❌ Error approving deletion: {str(e)}"
            )
        except:
            pass

@app.action("deny_deletion")
def handle_deny_deletion(ack, body, client, logger):
    ack()

    admin_id = body["user"]["id"]
    admin_name = body["user"]["name"]

    if not config.is_admin(admin_id):
        try:
            client.chat_postMessage(
                channel=admin_id,
                text="❌ You are not authorized to deny deletion requests."
            )
        except:
            pass
        return

    try:
        admin_message_ts = body["message"]["ts"]

        request = database.get_deletion_request_by_admin_message(admin_message_ts)

        if not request:
            raise ValueError("Deletion request not found in database")

        value_parts = body["actions"][0]["value"].split("|")
        requester_id = value_parts[2]

        database.update_deletion_request(
            request_id=request["id"],
            status="denied",
            admin_id=admin_id,
            admin_name=admin_name
        )

        updated_blocks = body["message"]["blocks"][:-1]
        updated_blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"❌ *Denied by <@{admin_id}> at <!date^{int(body['actions'][0]['action_ts'])}^{{date_short_pretty}} {{time}}|{body['actions'][0]['action_ts']}>*"
                }
            ]
        })

        client.chat_update(
            channel=body["channel"]["id"],
            ts=admin_message_ts,
            blocks=updated_blocks,
            text=f"Deletion request denied by {admin_name}"
        )

        client.chat_postMessage(
            channel=requester_id,
            text=f"❌ Your message deletion request has been denied by <@{admin_id}>."
        )

        logger.info(f"Deletion denied: ID={request['id']}, Admin={admin_id}")

    except Exception as e:
        logger.error(f"Error denying deletion: {e}")
        try:
            client.chat_postMessage(
                channel=admin_id,
                text=f"❌ Error denying deletion: {str(e)}"
            )
        except:
            pass

@app.event("app_home_opened")
def handle_app_home_opened(client, event, logger):
    user_id = event["user"]

    is_admin = config.is_admin(user_id)

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🗑️ Message Deletion App"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "This app allows you to request deletion of your own messages with admin approval."
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*How to use:*\n1. Right-click on any message you've posted\n2. Select 'Delete my message' from the shortcuts menu\n3. Wait for admin approval"
            }
        }
    ]

    if is_admin:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Admin Status:* ✅ You are an admin\n\nReview requests in <#{config.ADMIN_REVIEW_CHANNEL}>"
            }
        })

    client.views_publish(
        user_id=user_id,
        view={
            "type": "home",
            "blocks": blocks
        }
    )

if __name__ == "__main__":
    handler = SocketModeHandler(app, config.SLACK_APP_TOKEN)
    logger.info(f"⚡️ Slack app is running on port {config.PORT}!")
    handler.start()