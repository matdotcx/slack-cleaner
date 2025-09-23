# Slack Message Deletion App

A self-service Slack app that allows users to request deletion of their own messages with admin approval.

## Features

- **Message Shortcut**: Right-click any message and select "Delete my message"
- **Admin Approval Workflow**: Requests are posted to a private admin channel with Approve/Deny buttons
- **Audit Logging**: All deletion requests and actions are logged in a SQLite database
- **User Verification**: Only message authors can request deletion of their own messages
- **Real-time Updates**: Users receive DMs confirming approval/denial

## Prerequisites

- Python 3.8 or higher
- A Slack workspace where you have permission to install apps

## Setup

### 1. Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name your app (e.g., "Message Deletion Manager")
4. Select your workspace

### 2. Configure App Permissions

In your app settings, go to **OAuth & Permissions** and add these Bot Token Scopes:

- `channels:history`
- `channels:read`
- `chat:write`
- `groups:history`
- `groups:read`
- `im:history`
- `im:read`
- `im:write`
- `mpim:history`
- `mpim:read`
- `users:read`
- `commands`

### 3. Enable Message Shortcuts

1. Go to **Interactivity & Shortcuts**
2. Turn on Interactivity
3. Click "Create New Shortcut" → "On messages"
4. Name: `Delete my message`
5. Short Description: `Request deletion of this message`
6. Callback ID: `delete_my_message`

### 4. Enable Socket Mode

1. Go to **Socket Mode**
2. Enable Socket Mode
3. Generate an App-Level Token with `connections:write` scope
4. Save the token (starts with `xapp-`)

### 5. Install App to Workspace

1. Go to **Install App**
2. Click "Install to Workspace"
3. Authorize the app
4. Copy the Bot User OAuth Token (starts with `xoxb-`)
5. Copy the Signing Secret from **Basic Information**

### 6. Create Admin Review Channel

1. In Slack, create a private channel (e.g., `#deletion-requests`)
2. Invite your app to the channel: `/invite @YourAppName`
3. Copy the channel ID (right-click channel → View channel details)

### 7. (Optional) Create Audit Log Channel

1. Create another channel for audit logs (e.g., `#deletion-audit-log`)
2. Invite your app to the channel
3. Copy the channel ID

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd slack-cleaner
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your values:
```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-level-token

ADMIN_USER_IDS=U123456,U789012  # Comma-separated admin user IDs
ADMIN_REVIEW_CHANNEL=C123456789  # Channel ID for admin reviews
AUDIT_LOG_CHANNEL=C987654321  # (Optional) Channel ID for audit logs

PORT=3000
```

### Finding User IDs

1. In Slack, click on a user's profile
2. Click "More" → "Copy member ID"

### Finding Channel IDs

1. Right-click a channel
2. Select "View channel details"
3. Scroll down to find the Channel ID

## Running the App

### Local Development

```bash
python app.py
```

### Production Deployment

#### Railway

1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Create project: `railway init`
4. Add environment variables: `railway variables`
5. Deploy: `railway up`

#### Fly.io

1. Install Fly CLI: [https://fly.io/docs/hands-on/install-flyctl/](https://fly.io/docs/hands-on/install-flyctl/)
2. Login: `fly auth login`
3. Create app: `fly launch`
4. Set secrets:
```bash
fly secrets set SLACK_BOT_TOKEN=xoxb-...
fly secrets set SLACK_SIGNING_SECRET=...
fly secrets set SLACK_APP_TOKEN=xapp-...
# ... etc
```
5. Deploy: `fly deploy`

## Usage

### For Users

1. Right-click any message you've posted
2. Select "Delete my message" from the shortcuts menu
3. You'll receive a confirmation that your request was submitted
4. Wait for admin review
5. You'll receive a DM when your request is approved or denied

### For Admins

1. Deletion requests appear in the admin review channel
2. Click "Approve Deletion" to delete the message
3. Click "Deny Request" to reject the deletion
4. All actions are logged in the database

## Database

The app uses SQLite to store audit logs. The database file (`deletion_requests.db`) is created automatically on first run.

### Database Schema

```sql
deletion_requests (
    id,
    request_timestamp,
    message_ts,
    channel_id,
    channel_name,
    message_author_id,
    message_author_name,
    message_text,
    requester_id,
    requester_name,
    status,  -- 'pending', 'approved', 'denied', 'error'
    admin_id,
    admin_name,
    action_timestamp,
    admin_message_ts,
    notes
)
```

## Configuration Options

- `AUTO_APPROVE_MINUTES`: (Not implemented) Auto-approve deletions for messages under X minutes old
- `AUDIT_LOG_CHANNEL`: Optional channel for posting audit summaries

## Troubleshooting

### App not responding
- Check that Socket Mode is enabled
- Verify your App Token is correct
- Ensure the app is running (`python app.py`)

### Permission denied errors
- Verify all required scopes are added
- Re-install the app after adding new scopes

### Messages not being deleted
- Ensure the bot is invited to the channel where messages are being deleted
- Check admin permissions in the bot settings

## Security Notes

- Only message authors can request deletion of their own messages
- Only configured admins can approve/deny requests
- All actions are logged in the database
- Admin user IDs are verified before processing approvals/denials

## License

MIT