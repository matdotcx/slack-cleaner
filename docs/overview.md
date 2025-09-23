# Slack Message Deletion App - Overview

## What It Does

The Slack Message Deletion App is a self-service tool that allows Slack workspace members to request deletion of their own messages. It implements a workflow-based approval system where:

1. **Users** can right-click on any message they've posted and select "Delete my message" from the context menu
2. **Admins** receive deletion requests in a private review channel and can approve or deny them using emoji reactions (✅ for approve, ❌ for deny)
3. **The system** automatically deletes approved messages and notifies all parties of the outcome
4. **All actions** are logged in a SQLite database for audit purposes

## Why We Built It

### The Problem
In Slack workspaces, regular users cannot delete their own messages once posted. Only workspace admins have this ability, which creates several issues:

- Users must contact admins via DM to request message deletion
- No standardized process for tracking deletion requests
- No audit trail of what was deleted and why
- Admin time wasted on repetitive deletion tasks
- Inconsistent handling of deletion requests

### The Solution
This app automates and streamlines the entire message deletion workflow:

- **Self-service**: Users can request deletions themselves without DMing admins
- **Centralized review**: All requests appear in one dedicated channel
- **Audit logging**: Every request and action is recorded with timestamps
- **Transparency**: Optional public audit log for compliance
- **Efficiency**: Admins can approve/deny with a single emoji reaction

## How It Helps the Admin Team

### Time Savings
- **No more DMs**: Users no longer need to DM admins for deletions
- **Batch processing**: Admins can review multiple requests in one channel
- **Quick actions**: Approve/deny with a single emoji reaction (no typing required)
- **Automatic notifications**: Users are automatically informed of decisions

### Better Oversight
- **Centralized tracking**: All deletion requests in one place
- **Full audit trail**: Complete history of who requested what and when
- **Request details**: See the message content, channel, and requester before approving
- **Status tracking**: Database shows pending, approved, denied, and failed requests

### Risk Management
- **User verification**: System ensures only message authors can request deletion
- **Admin authorization**: Only configured admins can approve requests
- **Audit compliance**: Complete logs for compliance and review purposes
- **Error handling**: Clear error messages when deletions fail (e.g., bot not in channel)

### Workflow Example

1. **User posts something they want deleted** → Right-clicks message → Selects "Delete my message"
2. **Admin sees request** in #deletion-requests channel with full context:
   - Who requested it
   - What channel it's in
   - Message preview
   - Link to original message
3. **Admin reviews** → Adds ✅ reaction to approve or ❌ to deny
4. **Message deleted** immediately upon approval
5. **User notified** via DM of the outcome
6. **Action logged** in database for audit trail

## What Runs on the Hetzner Server

### Deployment Details

**Server**: Hetzner VPS (deadline.iaconelli.org)
**Application Directory**: `/opt/slack-cleaner/`
**Service**: Systemd service (`slack-cleaner.service`)

### Running Processes

The application runs as a single Python process that:

1. **Maintains WebSocket connection** to Slack via Socket Mode
2. **Listens for events**:
   - Message shortcut triggers ("Delete my message")
   - Emoji reaction events (admin approvals/denials)
   - App home opened events (user views app details)
3. **Manages SQLite database** for audit logging
4. **Sends notifications** to users and admins

### System Resources

- **Memory**: ~50-100MB RAM (lightweight Python process)
- **CPU**: Minimal (event-driven, mostly idle)
- **Storage**:
  - Application code: ~30KB
  - SQLite database: Grows with deletion requests (typically <1MB)
  - Python virtual environment: ~50MB
- **Network**: Persistent WebSocket connection to Slack (minimal bandwidth)

### Service Management

The app runs as a systemd service with:
- **Auto-start**: Starts automatically on server boot
- **Auto-restart**: Restarts automatically if it crashes
- **Logging**: All output goes to systemd journal
- **Monitoring**: Status can be checked with `systemctl status slack-cleaner`

### Maintenance Commands

```bash
# Check service status
sudo systemctl status slack-cleaner

# View logs (real-time)
sudo journalctl -u slack-cleaner -f

# View recent logs
sudo journalctl -u slack-cleaner -n 100

# Restart service (if needed)
sudo systemctl restart slack-cleaner

# Stop service
sudo systemctl stop slack-cleaner

# Start service
sudo systemctl start slack-cleaner
```

### Database Location

- **Path**: `/opt/slack-cleaner/deletion_requests.db`
- **Type**: SQLite
- **Purpose**: Stores all deletion request records
- **Backup**: Can be backed up by copying the .db file

### Configuration

All sensitive configuration is stored in environment variables (not in git):
- Slack tokens (bot and user)
- Admin user IDs
- Channel IDs for admin review and audit logging

These are loaded from the `/opt/slack-cleaner/.env` file on the server.

## Technical Architecture

### Why Socket Mode?
- **No public endpoints**: Doesn't require exposing web server to internet
- **No SSL configuration**: Slack handles all encryption via WebSocket
- **Firewall friendly**: Only outbound connection needed
- **Simple deployment**: Just run the Python script

### Why Emoji Reactions?
- **Reliable in Socket Mode**: Interactive buttons can have delivery issues
- **Simpler UX**: Admins just click emoji reactions
- **Visual feedback**: Can see who approved/denied at a glance
- **No additional permissions**: Works with standard Slack permissions

### Hybrid Token Approach
- **Bot Token**: Used for all messaging (DMs, admin messages, notifications)
- **User Token**: Required for actual message deletion (Slack API limitation)
- **Admin requirement**: User token must be from someone with access to all channels

## Security Considerations

1. **Authorization**: Only message authors can request deletion of their messages
2. **Admin verification**: Admin user IDs are verified before processing actions
3. **Audit trail**: Complete logging of all actions with timestamps
4. **Token security**: All tokens stored securely in .env file (not in git)
5. **Channel isolation**: Requests only processed in designated admin channel

## Benefits Summary

### For Users
- ✅ Self-service message deletion requests
- ✅ Clear status updates via DM
- ✅ No need to contact admins directly
- ✅ Transparent process

### For Admins
- ✅ Centralized request management
- ✅ Quick approval/denial (single emoji click)
- ✅ Full context before making decisions
- ✅ Complete audit trail
- ✅ Reduced interruptions from deletion requests

### For the Organization
- ✅ Standardized deletion process
- ✅ Compliance-ready audit logs
- ✅ Reduced admin overhead
- ✅ Better user experience
- ✅ Transparent operations

## Future Enhancements (Optional)

1. **Auto-approval rules**: Auto-approve deletions for messages under X minutes old
2. **Bulk operations**: Ability to approve multiple requests at once
3. **Statistics dashboard**: View metrics on deletion requests
4. **Retention policies**: Automatic cleanup of old audit records
5. **Additional notifications**: Slack webhooks for other systems

## Support

For any issues or questions about the app:
- Check the [readme.md](readme.md) for setup and troubleshooting
- View logs with `sudo journalctl -u slack-cleaner -f`
- Monitor the deletion requests database for audit information
- Contact the development team for feature requests or bugs