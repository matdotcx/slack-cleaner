# Slack Message Deletion App

A self-service Slack app for message deletion with admin approval workflow.

## Quick Links

- [Installation & Setup Guide](docs/readme.md)
- [Overview & Benefits](docs/overview.md)
- [Required API Scopes](docs/required-scopes.md)

## Quick Start

1. Set up the Slack app following [docs/readme.md](docs/readme.md)
2. Configure environment variables
3. Deploy to your server

## Documentation

All documentation is in the `/docs` folder:

- **[readme.md](docs/readme.md)** - Complete installation and setup instructions
- **[overview.md](docs/overview.md)** - What it does, why it exists, how it helps admins
- **[required-scopes.md](docs/required-scopes.md)** - Exact minimal API scopes needed

## Features

- Self-service message deletion requests
- Emoji-based admin approval (✅/❌)
- Complete audit trail in SQLite
- Automatic user notifications
- Runs via Socket Mode (no public endpoints needed)

## License

MIT