# Slack Message Deletion App

A self-service Slack app that allows users to request deletion of their own messages with admin approval workflow.

## Features

- **Self-Service Deletion Requests**: Users can request deletion of their own messages via right-click context menu
- **Emoji Reaction Approval**: Admins review and approve/deny requests using emoji reactions (✅/❌)
- **Full Audit Logging**: All deletion requests and actions are logged in SQLite database
- **User Notifications**: Automatic DM notifications for request status updates
- **Optional Audit Channel**: Public audit log channel for transparency
- **App Home**: Informative home tab with usage instructions
- **Hybrid Token Architecture**: Uses bot token for messaging and user token for deletions

## Architecture

- **Framework**: Python with Slack Bolt
- **Transport**: Socket Mode (WebSocket, no public endpoints required)
- **Database**: SQLite for audit trails
- **Authentication**: Hybrid approach using both bot and user tokens
- **Deployment**: Systemd service on Linux server

## Prerequisites

- Python 3.8 or higher
- A Slack workspace where you have permission to install apps
- Admin access to create User OAuth tokens

## Slack App Setup

### 1. Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name your app (e.g., "Message Deletion Manager")
4. Select your workspace

### 2. Configure Bot Token Scopes

In your app settings, go to **OAuth & Permissions** and add these Bot Token Scopes:

- `chat:write` - Send messages
- `users:read` - Read user information
- `channels:read` - Read channel information
- `groups:read` - Read private channel information
- `im:write` - Send DMs
- `im:read` - Read DMs
- `reactions:write` - Add reactions to messages
- `reactions:read` - Read reactions

### 3. Create User OAuth Token

**Important**: This requires workspace admin approval.

1. Go to **OAuth & Permissions**
2. Under "User Token Scopes", add:
   - `chat:write` - Delete messages as the user
   - `users:read` - Read user information
3. After adding scopes, reinstall the app to your workspace
4. Copy the User OAuth Token (starts with `xoxp-`)

### 4. Enable Message Shortcuts

1. Go to **Interactivity & Shortcuts**
2. Turn on Interactivity (no Request URL needed for Socket Mode)
3. Click "Create New Shortcut" → "On messages"
4. Name: `Delete my message`
5. Short Description: `Request deletion of this message`
6. Callback ID: `delete_my_message`

### 5. Enable Socket Mode

1. Go to **Socket Mode**
2. Enable Socket Mode
3. Click "Generate Token"
4. Token name: `socket-token`
5. Add scope: `connections:write`
6. Generate and save the token (starts with `xapp-`)

### 6. Enable Event Subscriptions

1. Go to **Event Subscriptions**
2. Enable Events
3. Under "Subscribe to bot events", add:
   - `reaction_added` - For admin approval/denial reactions
4. Save changes

### 7. Install App to Workspace

1. Go to **Install App**
2. Click "Install to Workspace"
3. Review and authorize the app
4. Copy the Bot User OAuth Token (starts with `xoxb-`)
5. Go to **Basic Information** and copy the Signing Secret

### 8. Create Admin Review Channel

1. In Slack, create a private channel (e.g., `#deletion-requests`)
2. Invite your app to the channel: `/invite @YourAppName`
3. Get channel ID:
   - Right-click channel → "View channel details"
   - Channel ID is at the bottom (starts with `C`)

### 9. (Optional) Create Audit Log Channel

1. Create another channel for audit logs (e.g., `#deletion-audit-log`)
2. Invite your app to the channel
3. Copy the channel ID

### 10. Get Admin User IDs

1. In Slack, click on each admin user's profile
2. Click "..." → "Copy member ID"
3. User IDs start with `U`

## Installation

1. Clone this repository:
```bash
git clone https://github.com/matdotcx/slack-cleaner.git
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

5. Edit `.env` with your Slack app credentials:
```env
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_USER_TOKEN=xoxp-your-user-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token

ADMIN_USER_IDS=U123456,U789012
ADMIN_REVIEW_CHANNEL=C123456789
AUDIT_LOG_CHANNEL=C987654321

PORT=3000
```

## Running the App

### Local Development

```bash
python app.py
```

The app will connect to Slack via Socket Mode and start listening for events.

### Production Deployment

#### Option 1: Systemd Service (Linux)

1. Copy files to server:
```bash
scp -r . user@server:/opt/slack-cleaner/
```

2. Create virtual environment on server:
```bash
ssh user@server
cd /opt/slack-cleaner
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Create systemd service file `/etc/systemd/system/slack-cleaner.service`:
```ini
[Unit]
Description=Slack Message Deletion App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/slack-cleaner
ExecStart=/usr/bin/python3 /opt/slack-cleaner/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

4. Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable slack-cleaner
sudo systemctl start slack-cleaner
sudo systemctl status slack-cleaner
```

5. View logs:
```bash
sudo journalctl -u slack-cleaner -f
```

#### Option 2: Docker

1. Build image:
```bash
docker build -t slack-cleaner .
```

2. Run container:
```bash
docker run -d \
  --name slack-cleaner \
  --env-file .env \
  --restart unless-stopped \
  slack-cleaner
```

#### Option 3: Fly.io

1. Install Fly CLI and login:
```bash
curl -L https://fly.io/install.sh | sh
fly auth login
```

2. Launch app:
```bash
fly launch
```

3. Set secrets:
```bash
fly secrets set SLACK_BOT_TOKEN=xoxb-...
fly secrets set SLACK_USER_TOKEN=xoxp-...
fly secrets set SLACK_SIGNING_SECRET=...
fly secrets set SLACK_APP_TOKEN=xapp-...
fly secrets set ADMIN_USER_IDS=U123456,U789012
fly secrets set ADMIN_REVIEW_CHANNEL=C123456789
fly secrets set AUDIT_LOG_CHANNEL=C987654321
```

4. Deploy:
```bash
fly deploy
```

## Usage

### For Users

1. **Request Deletion**:
   - Right-click on any message you've posted
   - Select "Delete my message" from the shortcuts menu
   - You'll receive a DM confirmation that your request was submitted

2. **Wait for Review**:
   - Admins will review your request in the admin channel
   - You'll receive a DM notification when approved or denied

3. **Important Notes**:
   - You can only request deletion of your own messages
   - Requests cannot be cancelled once submitted

### For Admins

1. **Review Requests**:
   - Deletion requests appear in the configured admin review channel
   - Each request shows the requester, channel, and message preview

2. **Approve or Deny**:
   - React with ✅ (`:white_check_mark:`) to **approve** and delete the message
   - React with ❌ (`:x:`) to **deny** the request
   - The message will be deleted immediately upon approval

3. **Important Notes**:
   - Only configured admins can approve/deny requests
   - All actions are logged in the database
   - The user who created the User OAuth Token must be a member of channels where messages are deleted

## Database

The app uses SQLite to store audit logs. The database file (`deletion_requests.db`) is created automatically on first run.

### Database Schema

```sql
CREATE TABLE deletion_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_ts TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    channel_name TEXT,
    message_author_id TEXT NOT NULL,
    message_author_name TEXT,
    message_text TEXT,
    requester_id TEXT NOT NULL,
    requester_name TEXT,
    admin_message_ts TEXT NOT NULL,
    status TEXT DEFAULT 'pending',  -- 'pending', 'approved', 'denied', 'error'
    admin_id TEXT,
    admin_name TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## Troubleshooting

### Common Issues

**1. Button clicks not working / Events not received**
- **Solution**: This app uses emoji reactions instead of interactive buttons due to Socket Mode limitations
- Ensure Event Subscriptions are enabled with `reaction_added` event subscribed
- Verify Socket Mode is enabled with a valid App-Level Token

**2. "channel_not_found" error when deleting messages**
- **Cause**: The user who created the User OAuth Token is not a member of the channel
- **Solution**: The admin user must join all channels where messages may be deleted
- Run: `/join #channel-name` for each channel

**3. App not responding to message shortcuts**
- Check that Socket Mode is enabled
- Verify the App Token (starts with `xapp-`) is correct
- Ensure the app is running: `sudo systemctl status slack-cleaner`
- Check logs: `sudo journalctl -u slack-cleaner -f`

**4. Permission errors / Missing scopes**
- Verify all required Bot Token Scopes are added (especially `reactions:write`)
- Add required User Token Scopes (`chat:write`)
- Reinstall the app after adding new scopes

**5. Database errors**
- Ensure the app has write permissions to the directory
- Check disk space is available
- Database file should be automatically created

### Debugging

**View app logs:**
```bash
# If using systemd
sudo journalctl -u slack-cleaner -f

# If running directly
python app.py
```

**Test database connection:**
```bash
sqlite3 deletion_requests.db "SELECT * FROM deletion_requests LIMIT 5;"
```

**Check running processes:**
```bash
ps aux | grep app.py
```

## Limitations

1. **Socket Mode Button Limitation**: Interactive buttons may not work reliably in Socket Mode due to multiple WebSocket connection issues. This app uses emoji reactions as a proven workaround.

2. **Channel Membership Requirement**: The user who created the User OAuth Token must be a member of all channels where messages need to be deleted.

3. **User Token Scope Approval**: User OAuth tokens with `chat:write` scope may require workspace admin approval during installation.

4. **Single Instance**: Only run one instance of the app per Slack app to avoid WebSocket connection conflicts.

## Security Considerations

- User tokens have elevated permissions - store securely and never commit to version control
- Only message authors can request deletion of their own messages
- Admin approval required for all deletions
- All actions are logged with timestamps and user information
- Admin user IDs are verified before processing any actions
- Audit logs are maintained in SQLite database for compliance

## Configuration Reference

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SLACK_BOT_TOKEN` | Bot User OAuth Token | `xoxb-...` |
| `SLACK_USER_TOKEN` | User OAuth Token for deletions | `xoxp-...` |
| `SLACK_SIGNING_SECRET` | App signing secret | `abc123...` |
| `SLACK_APP_TOKEN` | App-Level Token for Socket Mode | `xapp-...` |
| `ADMIN_USER_IDS` | Comma-separated admin user IDs | `U123,U456` |
| `ADMIN_REVIEW_CHANNEL` | Channel ID for admin reviews | `C123456789` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AUDIT_LOG_CHANNEL` | Channel ID for audit logs | None |
| `PORT` | Port number (informational) | `3000` |

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Technical Architecture Details

### Why Emoji Reactions Instead of Buttons?

During development, we discovered that interactive buttons don't work reliably in Socket Mode when multiple WebSocket connections are present. This is a known limitation where button interactions may not be delivered to the app. The emoji reaction approach is more reliable because:

1. Reactions are delivered via the `reaction_added` event
2. No interactive component registration required
3. Works consistently with Socket Mode
4. Simpler implementation with fewer moving parts

### Hybrid Token Approach

The app uses two types of tokens:

1. **Bot Token** (`SLACK_BOT_TOKEN`):
   - Used for all messaging operations
   - Sends DMs to users
   - Posts to admin review channel
   - Adds initial reactions to messages

2. **User Token** (`SLACK_USER_TOKEN`):
   - Required for deleting messages
   - Must be from a user who is a member of all channels
   - Provides the actual deletion capability

This hybrid approach provides a clean user experience while maintaining the necessary permissions for deletion.

## License

MIT