# Railway Deployment Guide

This guide walks you through deploying the Slack Message Deletion App to Railway with PostgreSQL.

## Prerequisites

- GitHub account
- Railway account (sign up at [railway.app](https://railway.app))
- Code pushed to a GitHub repository
- All required Slack tokens (see [required-scopes.md](required-scopes.md))

## Overview

Railway is a modern Platform-as-a-Service that makes deployment simple:
- Automatic deployments from GitHub
- Built-in PostgreSQL database
- Simple environment variable management
- No cold starts (your app stays running)
- $5/month free credit for testing

## Step 1: Push Code to GitHub

Ensure your latest code is pushed to GitHub:

```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

## Step 2: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Click "Login" and sign in with GitHub
3. Authorise Railway to access your repositories

## Step 3: Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your slack-cleaner repository
4. Railway will automatically detect the Python application

## Step 4: Add PostgreSQL Database

1. In your project dashboard, click "New"
2. Select "Database"
3. Choose "PostgreSQL"
4. Railway will automatically provision the database
5. The `DATABASE_URL` environment variable will be automatically set

## Step 5: Configure Environment Variables

1. Click on your service (not the database)
2. Go to the "Variables" tab
3. Click "Raw Editor" for easier bulk entry
4. Add all required environment variables:

```env
SLACK_BOT_TOKEN=xoxb-your-actual-bot-token
SLACK_USER_TOKEN=xoxp-your-actual-user-token
SLACK_SIGNING_SECRET=your-actual-signing-secret
SLACK_APP_TOKEN=xapp-your-actual-app-token
ADMIN_USER_IDS=U123456789,U987654321
ADMIN_REVIEW_CHANNEL=C123456789
AUDIT_LOG_CHANNEL=C987654321
ALLOW_ALL_CHANNEL_MEMBERS=false
PORT=3000
```

**Important Notes:**
- Do NOT set `DATABASE_URL` manually - Railway sets this automatically
- Replace all example values with your actual Slack tokens
- Find Slack user IDs: Click on a user → View profile → More → Copy member ID
- Find channel IDs: Right-click channel → View channel details → Copy channel ID

## Step 6: Deploy

1. Railway will automatically deploy after you add environment variables
2. Watch the deployment logs in the "Deployments" tab
3. Wait for "Build successful" and "Deployment successful" messages

## Step 7: Verify Deployment

Check the logs to ensure the app started successfully:

1. Go to the "Deployments" tab
2. Click on the latest deployment
3. View the logs
4. Look for: `⚡️ Slack app is running on port 3000!`

## Step 8: Test the Application

1. Go to your Slack workspace
2. Find a message you sent
3. Right-click the message → "Delete my message"
4. Check the admin review channel for the deletion request
5. React with ✓ to approve

If everything works, your app is successfully deployed!

## Database Migration (Optional)

If you have existing data in a SQLite database from a previous deployment, you can migrate it to PostgreSQL.

### Export from SQLite

On your old server:

```bash
# Connect to SQLite database
sqlite3 deletion_requests.db

# Export to SQL file
.output export.sql
.dump deletion_requests
.quit
```

### Import to PostgreSQL

Get your DATABASE_URL from Railway:

1. Go to your PostgreSQL service
2. Click "Connect"
3. Copy the "Postgres Connection URL"

Then import:

```bash
# Connect to Railway PostgreSQL
psql "your-railway-database-url-here"

# Run the exported SQL
\i export.sql
```

## Automatic Deployments

Railway automatically deploys when you push to your main branch:

```bash
git add .
git commit -m "Update feature"
git push origin main
```

Railway will detect the push and deploy automatically.

## Monitoring and Logs

### View Logs

1. Go to your project dashboard
2. Click on your service
3. Go to "Deployments" tab
4. Click on the active deployment
5. View real-time logs

### Monitor Resource Usage

1. Go to "Metrics" tab
2. View CPU, memory, and network usage
3. Adjust resources if needed (paid plans only)

## Scaling

Railway automatically handles:
- Automatic restarts on failure (up to 10 retries)
- Resource allocation
- Network connectivity

For higher traffic, you can upgrade to a paid plan and adjust resources.

## Troubleshooting

### App Not Starting

Check logs for errors:
- Missing environment variables
- Database connection issues
- Slack token problems

### Database Connection Errors

1. Verify PostgreSQL service is running
2. Check that DATABASE_URL is set automatically
3. Ensure database service is in the same project

### Slack Events Not Working

1. Verify Socket Mode is enabled in Slack app settings
2. Check SLACK_APP_TOKEN is correct
3. Ensure app is running (check logs)

### Deployment Fails

1. Check build logs for Python errors
2. Verify requirements.txt is correct
3. Ensure Python version compatibility (3.11+)

## Cost Estimate

Railway pricing:
- Free tier: $5/month credit (sufficient for testing)
- Developer plan: $5/month subscription + usage
- Typical usage for this app: ~$2-5/month

Components:
- Web service: ~$1-3/month
- PostgreSQL: ~$1-2/month
- Total: ~$2-5/month (free tier covers testing)

## Alternative: Render

If you prefer Render over Railway, see the deployment differences:

**Railway Advantages:**
- No cold starts
- Simpler setup
- Better free tier for this use case

**Render Limitations:**
- Free tier services spin down after 15 minutes of inactivity
- Cold starts can cause Slack event timeouts
- Requires paid plan for always-on service

## Migrating from VPS

If you're migrating from a VPS systemd service:

1. **Stop the VPS service:**
   ```bash
   sudo systemctl stop slack-cleaner
   sudo systemctl disable slack-cleaner
   ```

2. **Export SQLite data** (if you want to preserve history):
   ```bash
   cd /opt/slack-cleaner
   sqlite3 deletion_requests.db .dump > export.sql
   ```

3. **Deploy to Railway** (follow steps above)

4. **Import data to PostgreSQL** (optional)

5. **Test thoroughly** before decommissioning VPS

6. **Remove VPS service:**
   ```bash
   sudo rm /etc/systemd/system/slack-cleaner.service
   sudo systemctl daemon-reload
   ```

## Support

For Railway-specific issues:
- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway

For app-specific issues:
- Check application logs
- Review Slack app configuration
- Verify environment variables

## Next Steps

After successful deployment:
1. Monitor logs for a few days
2. Test all features (approval, denial, error handling)
3. Set up alerts for failures (Railway paid plans)
4. Consider backing up PostgreSQL data periodically
