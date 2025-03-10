# D2Tracker

A Python-based tracker for Diablo Clone (DClone) progress and Terror Zones in Diablo 2: Resurrected. This application connects to d2emu.com's websocket API to monitor DClone status and Terror Zone rotations, sending notifications to Discord when changes occur.

## Features

- Real-time DClone progress tracking for hardcore ladder (US, Europe, Asia)
- Terror Zone tracking with tier information
- Discord webhook notifications
- Docker support

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Discord webhook URL for notifications
DCLONE_WEBHOOK=your_discord_webhook_url
TZONE_WEBHOOK=your_discord_webhook_url

# Discord notification mentions
DCLONE_NOTIFY=@role_or_user_mention
TZONE_NOTIFY=@role_or_user_mention

# d2emu.com API authentication
D2EMU_AUTH=your_auth_token
```
