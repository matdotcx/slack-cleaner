# Required Slack API Scopes

This document lists the **exact and minimal** scopes needed for the Slack Message Deletion App to function.

## Bot Token Scopes

Configure these under **OAuth & Permissions** → **Bot Token Scopes**:

| Scope | Purpose | Used For |
|-------|---------|----------|
| `chat:write` | Post messages | Sending DMs, posting to admin channel, update messages |
| `users:read` | View users | Getting user names for notifications |
| `channels:read` | View channels | Getting channel names for context |
| `groups:read` | View private channels | Getting private channel names |
| `im:write` | Send DMs | Notifying users of request status |
| `reactions:write` | Add reactions | Adding ✅ and ❌ reactions to admin messages |

**Total: 6 bot scopes**

## User Token Scopes

Configure these under **OAuth & Permissions** → **User Token Scopes**:

| Scope | Purpose | Used For |
|-------|---------|----------|
| `chat:write` | Delete messages | Deleting approved messages |

**Total: 1 user scope**

## App-Level Token

Configure this under **Basic Information** → **App-Level Tokens**:

| Scope | Purpose | Used For |
|-------|---------|----------|
| `connections:write` | WebSocket connections | Socket Mode connectivity |

**Total: 1 app-level scope**

## Events to Subscribe To

Under **Event Subscriptions** → **Subscribe to bot events**:

| Event | Purpose |
|-------|---------|
| `reaction_added` | Detect admin approval/denial reactions |

## Interactive Components

Under **Interactivity & Shortcuts**:

- **Message Shortcut**: Create shortcut with callback ID `delete_my_message`

## Scopes NOT Needed

The following scopes are **NOT required** and should be avoided:
- ❌ `channels:history` - Not needed
- ❌ `channels:write` - Not needed
- ❌ `groups:history` - Not needed
- ❌ `groups:write` - Not needed
- ❌ `im:history` - Not needed
- ❌ `im:read` - Not needed
- ❌ `mpim:history` - Not needed
- ❌ `mpim:read` - Not needed
- ❌ `mpim:write` - Not needed
- ❌ `reactions:read` - Not needed (event gives us reaction info)
- ❌ `commands` - Not needed (app uses message shortcuts, not slash commands)
- ❌ `users:write` - Not needed
- ❌ Any admin scopes - Not needed

## Summary

**Minimum scopes required:**
- Bot Token: 6 scopes
- User Token: 1 scope
- App-Level Token: 1 scope
- Events: 1 event subscription
- Shortcuts: 1 message shortcut

This minimal scope configuration follows the principle of least privilege and reduces the security review burden for workspace admins.